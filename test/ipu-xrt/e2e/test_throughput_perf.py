# This file is licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# (c) Copyright 2023 AMD Inc.


from contextlib import ExitStack
import numbers
from pathlib import Path
import sys

from numpy.lib.stride_tricks import as_strided

from aie.compiler.aiecc.main import emit_design_kernel_json
from aie.compiler.util import (
    compile_with_vectorization,
    compile_without_vectorization,
    make_xclbin,
)
from aie.dialects import aie, aievec, aiex
from aie.dialects.aie import (
    AIEDevice,
    DMAChannelDir,
    LockAction,
    WireBundle,
    bd_dim_layout,
)
from aie.dialects.transform import any_op_t, apply_registered_pass, get_parent_op
from aie.dialects.transform.extras import named_sequence
from aie.dialects.transform.loop import loop_unroll
from aie.dialects.transform.structured import structured_match
from aie.extras.runtime.passes import Pipeline, run_pipeline
from aie.dialects import aie, aievec, aiex, builtin, pdl, vector
from aie.extras.util import bb, find_ops
from aie.dialects.aiex import TileArray
from aie.extras.context import ExplicitlyManagedModule

# noinspection PyUnresolvedReferences
from aie.extras.dialects.ext import arith, func, linalg, memref, scf, vector

# noinspection PyUnresolvedReferences
from aie.extras.testing import MLIRContext, filecheck, mlir_ctx as ctx
import aie.extras.types as T
from aie.ir import UnitAttr, StringAttr
from aie.util import tiling_calculator_n_tiles
from aie.xrt import XCLBin
from filelock import FileLock
import numpy as np
import pytest

# needed since the fix isn't defined here nor conftest.py
pytest.mark.usefixtures("ctx")


range_ = scf.range_
yield_ = scf.yield_

DMA = WireBundle.DMA
S2MM = DMAChannelDir.S2MM
MM2S = DMAChannelDir.MM2S
Acquire = LockAction.Acquire
AcquireGreaterEqual = LockAction.AcquireGreaterEqual
Release = LockAction.Release


def test_tiled_nonsquare_tile_matrix_mult_vectorized_sugar(
    ctx: MLIRContext, workdir: Path
):
    M, K, N = 32, 32, 32

    @func.func(sym_visibility="private")
    def matmul_f32_f32(
        A: T.memref(M, K, T.f32()),
        B: T.memref(K, N, T.f32()),
        C: T.memref(M, N, T.f32()),
    ):
        linalg.matmul(A, B, C)

    mod_aie = ExplicitlyManagedModule()

    @aie.device(AIEDevice.ipu)
    def ipu():
        matmul_f32_f32.emit(decl=True)
        tile_0_0 = aie.tile(0, 0)
        tile_0_2 = aie.tile(0, 2)

        # in
        buffer_0_2_a = aie.buffer(tile_0_2, (M, K), T.f32())
        buffer_0_2_b = aie.buffer(tile_0_2, (K, N), T.f32())
        # out
        buffer_0_2_c = aie.buffer(tile_0_2, (M, N), T.f32())

        # input
        lock_0_2_read_in_a = aie.lock(tile_0_2, init=1)
        lock_0_2_read_in_b = aie.lock(tile_0_2, init=1)
        lock_0_2_use_a = aie.lock(tile_0_2, init=0)
        lock_0_2_use_b = aie.lock(tile_0_2, init=0)
        lock_0_2_use_c = aie.lock(tile_0_2, init=1)
        lock_0_2_write_out_c = aie.lock(tile_0_2, init=0)

        aie.flow(tile_0_0, DMA, 0, tile_0_2, DMA, 0)
        aie.flow(tile_0_0, DMA, 1, tile_0_2, DMA, 1)
        aie.flow(tile_0_2, DMA, 0, tile_0_0, DMA, 0)

        @aie.mem(tile_0_2)
        def mem_0_2():
            aiex.receive_bd(0, lock_0_2_read_in_a, buffer_0_2_a, lock_0_2_use_a)
            aiex.receive_bd(1, lock_0_2_read_in_b, buffer_0_2_b, lock_0_2_use_b)
            aiex.send_bd(0, lock_0_2_write_out_c, buffer_0_2_c, lock_0_2_use_c)
            aie.end()

        @aie.core(tile_0_2)
        def core():
            with (
                aiex.hold_lock(lock_0_2_use_a, lock_0_2_read_in_a),
                aiex.hold_lock(lock_0_2_use_b, lock_0_2_read_in_b),
                aiex.hold_lock(lock_0_2_use_c, lock_0_2_write_out_c),
            ):
                linalg.fill(0, buffer_0_2_c)
                matmul_f32_f32(buffer_0_2_a, buffer_0_2_b, buffer_0_2_c)

    mod_aie.finish()
    mod_aievec = ExplicitlyManagedModule()

    @builtin.module(attrs={"transform.target_tag": StringAttr.get("payload")})
    def payload():
        matmul_f32_f32.emit(force=True)

    @builtin.module(attrs={"transform.with_named_sequence": UnitAttr.get()})
    def mod_transform():
        @named_sequence("affine_unroll", [any_op_t()], [])
        def affine_unroll(target: any_op_t()):
            func = structured_match(any_op_t(), target, ops=["func.func"])
            new_func = apply_registered_pass(
                any_op_t(), func, "convert-linalg-to-affine-loops"
            )
            m = structured_match(any_op_t(), new_func, ops=["arith.addf"])
            loop = get_parent_op(pdl.op_t(), m, op_name="affine.for")
            # unroll inner loop
            loop_unroll(loop, 16)

        @named_sequence("affine_super_vectorize", [any_op_t()], [])
        def super_vectorize(target: any_op_t()):
            func = structured_match(any_op_t(), target, ops=["func.func"])
            func = apply_registered_pass(
                any_op_t(),
                func,
                "affine-super-vectorize",
                options="virtual-vector-size=16",
            )
            func = apply_registered_pass(any_op_t(), func, "canonicalize")
            mod = apply_registered_pass(
                any_op_t(),
                target,
                "convert-vector-to-aievec",
                options="aie-target=aieml",
            )

    mod_aievec.finish()

    affine_loops = run_pipeline(
        mod_aievec,
        Pipeline()
        .transform_interpreter(
            entry_point="affine_unroll",
            debug_payload_root_tag="payload",
        )
        .canonicalize()
        .cse(),
    )

    super_vec = run_pipeline(
        affine_loops,
        Pipeline()
        .transform_interpreter(
            entry_point="affine_super_vectorize",
            debug_payload_root_tag="payload",
        )
        .lower_affine(),
    )

    mod_aievec = find_ops(
        super_vec.operation,
        lambda x: "transform.target_tag" in x.attributes,
        single=True,
    )

    compile_with_vectorization(mod_aie, mod_aievec, workdir)
    # compile_without_vectorization(mod_aie, workdir)

    ipu_insts = aiex.ipu.get_prolog()
    xclbin_path = make_xclbin(mod_aie, workdir)
    with FileLock("/tmp/ipu.lock"):
        xclbin = XCLBin(xclbin_path, "MLIR_AIE")
        views = xclbin.mmap_buffers([(M, K), (K, M), (M, N)], np.float32)

        col = 0
        lengths = [M * K, K * N, M * N]
        bd_id_direction = [MM2S, MM2S, S2MM]
        shim_channels = [0, 1, 0]
        for i, (len, bd_id_dir, shim_ch) in enumerate(
            zip(lengths, bd_id_direction, shim_channels)
        ):
            bd_id = buffer_idx = i
            writebd_shimtile_insts = aiex.ipu.writebd_shimtile(
                column=col, bd_id=bd_id, buffer_length=len
            )
            ipu_insts.extend(
                aiex.ipu._exec_write_bd_extend_shim_tile_opt(
                    writebd_shimtile_insts,
                    tensor_addr=xclbin._get_buffer_host_address(buffer_idx),
                )
            )
            ipu_insts.extend(
                aiex.ipu.shimtile_push_queue(
                    channel_dir=bd_id_dir,
                    channel_index=shim_ch,
                    column=col,
                    bd_id=bd_id,
                )
            )

        ipu_insts.extend(
            aiex.ipu.sync(column=col, channel=shim_channels[2], direction=S2MM)
        )

        xclbin.load_ipu_instructions(ipu_insts)

        wrap_A = np.asarray(views[0])
        wrap_B = np.asarray(views[1])
        wrap_C = np.asarray(views[2])

        A = np.ones((M, K)).astype(np.float32)
        B = np.ones((K, N)).astype(np.float32)
        C = np.zeros((M, N), dtype=np.float32)

        np.copyto(wrap_A, A, casting="no")
        np.copyto(wrap_B, B, casting="no")
        np.copyto(wrap_C, C, casting="no")

        xclbin.sync_buffers_to_device()
        xclbin.run()
        print("Running kernel")
        xclbin.wait(30)
        xclbin.sync_buffers_from_device()

        if not np.array_equal(A @ B, wrap_C):
            with np.printoptions(threshold=sys.maxsize, linewidth=sys.maxsize):
                print(A @ B)
                print(wrap_C)
                assert False


def extract_patches(
    arr,
    patch_shape: int | tuple[int, ...] | list[int, ...] = 8,
    extraction_step: int | tuple[int, ...] | list[int, ...] = None,
):
    if extraction_step is None:
        extraction_step = patch_shape
    arr_ndim = arr.ndim

    if isinstance(patch_shape, numbers.Number):
        patch_shape = tuple([patch_shape] * arr_ndim)
    if isinstance(extraction_step, numbers.Number):
        extraction_step = tuple([extraction_step] * arr_ndim)

    patch_strides = arr.strides

    slices = tuple(slice(None, None, st) for st in extraction_step)
    # grab the elements at the starts of the "extraction steps"
    # and get the strides to those elements
    indexing_strides = arr[slices].strides

    patch_indices_shape = (
        (np.array(arr.shape) - np.array(patch_shape)) // np.array(extraction_step)
    ) + 1

    shape = tuple(list(patch_indices_shape) + list(patch_shape))
    strides = tuple(list(indexing_strides) + list(patch_strides))

    patches = as_strided(arr, shape=shape, strides=strides)
    return patches


def test_tiled_nonsquare_tile_spatial_4x4_broadcast(ctx: MLIRContext, workdir: Path):

    cols = [0, 1, 2, 3]
    core_rows = [2, 3, 4, 5]
    rows = [0, 1, *core_rows]

    m, k, n = 32, 32, 32
    per_col = 2048 // len(cols)
    M, K, N = 32, per_col, 32

    shim_channels = {}
    iters = per_col // k

    @aie.device(AIEDevice.ipu)
    def ipu():
        tiles = TileArray(cols, rows)
        aie.slsl("shim to mem a")
        tiles[cols, 0].flow(tiles[cols, 1], source_annot="a", dest_annot="a")
        aie.slsl("shim to mem b")
        tiles[cols, 0].flow(tiles[cols, 1], source_annot="b", dest_annot="b")

        for col in cols:
            # broadcast out to the row
            aie.slsl(f"col={col} send a to col {col}")
            tiles[col, 1].flow(tiles[col, 2:], source_annot="a", dest_annot="a")

        for col in cols:
            # broadcast out to the col
            aie.slsl(f"col={col} send b to row {col + 2}")
            tiles[col, 1].flow(tiles[:, col + 2], source_annot="b", dest_annot="b")

        for col in cols:
            # get result back
            aie.slsl(f"return c from col {col}")
            tiles[col, 1].rflow(tiles[col, 2:], source_annot="c", dest_annot="c")

        aie.slsl("mem to shim")
        tiles[cols, 1].flow(tiles[cols, 0], source_annot="c", dest_annot="c")

        for t in tiles[cols, 0]:
            out_a_fl = t.flows(filter_source=True, source_annot="a", single=True)
            out_b_fl = t.flows(filter_source=True, source_annot="b", single=True)
            shim_channels[int(t.tile.col), 0] = int(out_a_fl.source_channel)
            shim_channels[int(t.tile.col), 1] = int(out_b_fl.source_channel)

            in_c_fl = t.flows(filter_dest=True, dest_annot="c")
            shim_channels[int(t.tile.col), 2] = int(in_c_fl.dest_channel)

        aie.slsl("configure mem tile dmas")
        for t in tiles[cols, 1]:
            in_a_fl = t.flows(filter_dest=True, dest_annot="a", single=True)
            out_a_fl = t.flows(filter_source=True, source_annot="a", single=True)
            in_b_fl = t.flows(filter_dest=True, dest_annot="b", single=True)
            out_b_fl = t.flows(filter_source=True, source_annot="b", single=True)
            in_c_1_fl, in_c_2_fl, in_c_3_fl, in_c_4_fl = t.flows(
                filter_dest=True, dest_annot="c"
            )
            out_c_fl = t.flows(filter_source=True, source_annot="c")

            A = aie.buffer(t.tile, (M, K), dtype=T.f32())
            B = aie.buffer(t.tile, (K, N), dtype=T.f32())
            # transpose so it's easier to write to
            C = aie.buffer(t.tile, (len(cols) * N, M), dtype=T.f32())

            in_A_lock = aie.lock(t.tile, init=1)
            out_A_lock = aie.lock(t.tile, init=0)
            in_B_lock = aie.lock(t.tile, init=1)
            out_B_lock = aie.lock(t.tile, init=0)

            in_C_lock = aie.lock(t.tile, init=0)

            @aie.memtile_dma(t.tile)
            def mem():
                # fmt: off
                aiex.receive_bd(in_a_fl.dest_channel, in_A_lock, A, out_A_lock, loop=False)
                aiex.send_bd(out_a_fl.source_channel, out_A_lock, A, rel_val=0,
                    dims=[(32, 512), (32, 1)], len=m * k, iter=(16, 32), repeat_count=iters - 1
                )

                aiex.receive_bd(in_b_fl.dest_channel, in_B_lock, B, out_B_lock, loop=False)
                aiex.send_bd(out_b_fl.source_channel, out_B_lock, B, rel_val=0,
                    len=k * n, iter=(iters, k * n), repeat_count=iters - 1
                )

                aiex.receive_bd(in_c_1_fl.dest_channel, in_C_lock, C, acq_action=Acquire, acq_val=0, len=N * M, offset=0 * N * M, repeat_count=iters - 1)
                aiex.receive_bd(in_c_2_fl.dest_channel, in_C_lock, C, acq_action=Acquire, acq_val=1, len=N * M, offset=1 * N * M, repeat_count=iters - 1)
                aiex.receive_bd(in_c_3_fl.dest_channel, in_C_lock, C, acq_action=Acquire, acq_val=2, len=N * M, offset=2 * N * M, repeat_count=iters - 1)
                aiex.receive_bd(in_c_4_fl.dest_channel, in_C_lock, C, acq_action=Acquire, acq_val=3, len=N * M, offset=3 * N * M, repeat_count=iters - 1)

                aiex.send_bd(out_c_fl.source_channel, in_C_lock,  C, acq_val=4, repeat_count=iters - 1)
                # fmt: on

                aie.end()

        aie.slsl("configure core mem dmas")
        for t in list(tiles[cols, 2:]):
            in_a_fl = t.flows(filter_dest=True, dest_annot="a")
            in_b_fl = t.flows(filter_dest=True, dest_annot="b")
            out_c_fl = t.flows(filter_source=True, source_annot="c")

            in_a_prod_lock = aie.lock(t.tile, init=1)
            in_a_cons_lock = aie.lock(t.tile, init=0)
            in_b_prod_lock = aie.lock(t.tile, init=1)
            in_b_cons_lock = aie.lock(t.tile, init=0)
            out_c_prod_lock = aie.lock(t.tile, init=1)
            out_c_cons_lock = aie.lock(t.tile, init=0)

            a_buffer = t.buffer([(m, k)], T.f32(), annot="a")
            b_buffer = t.buffer([(k, n)], T.f32(), annot="b")
            c_buffer = t.buffer([(m, n)], T.f32(), annot="c")

            @aie.mem(t.tile)
            def mem():
                # fmt: off
                aiex.receive_bd(int(in_a_fl.dest_channel), in_a_prod_lock, a_buffer, in_a_cons_lock, repeat_count=iters - 1)
                aiex.receive_bd(int(in_b_fl.dest_channel), in_b_prod_lock, b_buffer, in_b_cons_lock, repeat_count=iters - 1)
                aiex.send_bd(int(out_c_fl.source_channel), out_c_cons_lock, c_buffer, out_c_prod_lock, repeat_count=iters - 1)
                # fmt: on

                aie.end()

            @aie.core(t.tile, elf_file="core_0_2.elf")
            def core():
                linalg.fill(0, c_buffer)
                for _ in range_(iters):
                    with (
                        aiex.hold_lock(in_a_cons_lock, in_a_prod_lock),
                        aiex.hold_lock(in_b_cons_lock, in_b_prod_lock),
                        aiex.hold_lock(out_c_prod_lock, out_c_cons_lock),
                    ):
                        linalg.matmul(a_buffer, b_buffer, c_buffer)
                    yield_()

    print(ctx.module)

    compile_without_vectorization(ctx.module, workdir, template_core=(0, 2))
    buffer_args = list(
        zip(
            [f"col_{c}_a" for c in cols],
            [f"col_{c}_b" for c in cols],
            [f"col_{c}_c" for c in cols],
        )
    )
    buffer_args = [a for col in buffer_args for a in col]
    kernel_json = emit_design_kernel_json(buffer_args=buffer_args)
    xclbin_path = make_xclbin(ctx.module, workdir, kernel_json=kernel_json)

    ipu_insts = aiex.ipu.get_prolog()
    bd_id_direction = {0: MM2S, 1: MM2S, 2: S2MM}
    buffer_lengths = []
    for a in buffer_args:
        if "_a" in a:
            buffer_lengths.append((M, K))
        elif "_b" in a:
            buffer_lengths.append((K, N))
        elif "_c" in a:
            buffer_lengths.append((len(cols) * N, M))

    with FileLock("/tmp/ipu.lock"):
        xclbin = XCLBin(xclbin_path, "MLIR_AIE")
        views = xclbin.mmap_buffers(buffer_lengths, np.float32)
        buffer_idx = -1
        for col in cols:
            for bd_id in [0, 1, 2]:
                buffer_idx += 1
                writebd_shimtile_insts = aiex.ipu.writebd_shimtile(
                    column=col,
                    bd_id=bd_id,
                    buffer_length=np.prod(buffer_lengths[buffer_idx]),
                )
                ipu_insts.extend(
                    aiex.ipu._exec_write_bd_extend_shim_tile_opt(
                        writebd_shimtile_insts,
                        tensor_addr=xclbin._get_buffer_host_address(buffer_idx),
                    )
                )
                ipu_insts.extend(
                    aiex.ipu.shimtile_push_queue(
                        channel_dir=bd_id_direction[bd_id],
                        channel_index=shim_channels[col, bd_id],
                        column=col,
                        bd_id=bd_id,
                        # repeats=iters - 1,
                    )
                )

        for col in cols:
            bd_id = 2
            dest_channel = shim_channels[col, bd_id]
            ipu_insts.extend(
                aiex.ipu.sync(column=col, channel=dest_channel, direction=S2MM)
            )

        xclbin.load_ipu_instructions(ipu_insts)

        As = {c: np.random.randint(0, 10, (M, K)).astype(np.float32) for c in cols}
        Bs = {c: np.random.randint(0, 10, (K, N)).astype(np.float32) for c in cols}
        Cs = {c: np.zeros((len(cols) * N, M), dtype=np.float32) for c in cols}
        wraps = list(map(np.asarray, views))
        for col in cols:
            np.copyto(wraps[3 * col + 0], As[col], casting="no")
            np.copyto(wraps[3 * col + 1], Bs[col], casting="no")
            np.copyto(wraps[3 * col + 2], Cs[col], casting="no")

        xclbin.sync_buffers_to_device()
        xclbin.run()
        print("Running kernel")
        xclbin.wait(30)
        xclbin.sync_buffers_from_device()

        with np.printoptions(threshold=sys.maxsize, linewidth=sys.maxsize):
            for col in cols:
                print()
                print(As[col] @ Bs[col])
                print()
                print(wraps[3 * col + 2])