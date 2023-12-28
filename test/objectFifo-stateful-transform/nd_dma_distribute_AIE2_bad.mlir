//===- nd_dma_distribute_AIE2_bad.mlir -------------------------*- MLIR -*-===//
//
// This file is licensed under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// Copyright (C) 2023, Advanced Micro Devices, Inc.
//
//===----------------------------------------------------------------------===//

// RUN: aie-opt --aie-objectFifo-stateful-transform --verify-diagnostics %s

module @ndDMAObjFifoAIE2 {
 aie.device(xcve2302) {
    %tile10 = aie.tile(1, 0)
    %tile11 = aie.tile(1, 1)
    %tile22 = aie.tile(2, 2)
    %tile23 = aie.tile(2, 3)

    aie.objectfifo @of0 (%tile10, {%tile11 fromStream [<wrap = 32, step = 16>,
                                                       <wrap = 8,  step = 1>]},
                         2 : i32) : !aie.objectfifo<memref<256xi32>>

    aie.objectfifo @of1 (%tile11 toStream [<wrap = 4, step = 64>,
                                           <wrap = 2, step = 4>,
                                           <wrap = 8, step = 8>,
                                           <wrap = 4, step = 1>],
                        {%tile22}, 2 : i32) : !aie.objectfifo<memref<128xi32>>

    aie.objectfifo @of2 (%tile11 toStream [<wrap = 4, step = 64>,
                                           <wrap = 2, step = 4>,
                                           <wrap = 8, step = 8>,
                                           <wrap = 4, step = 1>],
                        {%tile23}, 2 : i32) : !aie.objectfifo<memref<128xi32>>
   // expected-error@+1 {{'aie.objectfifo.link' op currently does not support objectFifos with dimensionsFromStreamPerConsumer.}}
   aie.objectfifo.link [ @of0 ] -> [ @of1, @of2 ] ()
 }
}