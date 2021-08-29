//===- test.cpp -------------------------------------------------*- C++ -*-===//
//
// This file is licensed under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// (c) Copyright 2020 Xilinx Inc.
//
//===----------------------------------------------------------------------===//

#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <thread>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <xaiengine.h>
#include "test_library.h"

#define XAIE_NUM_ROWS            8
#define XAIE_NUM_COLS           50
#define XAIE_ADDR_ARRAY_OFF     0x800

#define LOCK_TIMEOUT 100

#define HIGH_ADDR(addr)	((addr & 0xffffffff00000000) >> 32)
#define LOW_ADDR(addr)	(addr & 0x00000000ffffffff)

#define MLIR_STACK_OFFSET 4096

namespace {

XAieGbl_Config *AieConfigPtr;	                          /**< AIE configuration pointer */
XAieGbl AieInst;	                                      /**< AIE global instance */
XAieGbl_HwCfg AieConfig;                                /**< AIE HW configuration instance */
XAieGbl_Tile TileInst[XAIE_NUM_COLS][XAIE_NUM_ROWS+1];  /**< Instantiates AIE array of [XAIE_NUM_COLS] x [XAIE_NUM_ROWS] */
XAieDma_Tile TileDMAInst[XAIE_NUM_COLS][XAIE_NUM_ROWS+1];

#include "aie_inc.cpp"

}

int
main(int argc, char *argv[])
{
    printf("test start.\n");

    size_t aie_base = XAIE_ADDR_ARRAY_OFF << 14;
    XAIEGBL_HWCFG_SET_CONFIG((&AieConfig), XAIE_NUM_ROWS, XAIE_NUM_COLS, XAIE_ADDR_ARRAY_OFF);
    XAieGbl_HwInit(&AieConfig);
    AieConfigPtr = XAieGbl_LookupConfig(XPAR_AIE_DEVICE_ID);
    XAieGbl_CfgInitialize(&AieInst, &TileInst[0][0], AieConfigPtr);

    mlir_configure_cores();
    mlir_configure_switchboxes();
    mlir_configure_dmas();
    mlir_initialize_locks();

    int errors = 0;

    printf("Acquire input buffer lock first.\n");
    XAieTile_LockAcquire(&(TileInst[1][3]), 3, 0, 0); // Should this part of setup???

    ACDC_clear_tile_memory(TileInst[1][3]);
    ACDC_clear_tile_memory(TileInst[3][3]);
    mlir_write_buffer_a13(3, 7); // set input value

    ACDC_check("Before start cores:", mlir_read_buffer_a13(3), 7, errors);
    ACDC_check("Before start cores:", mlir_read_buffer_b13(5), 0, errors);
    ACDC_check("Before start cores:", mlir_read_buffer_a33(5), 0, errors);
    ACDC_check("Before start cores:", mlir_read_buffer_b33(5), 0, errors);

    printf("Start cores\n");
    mlir_start_cores();

    ACDC_check("Before release lock:", mlir_read_buffer_a13(3), 7, errors);
    ACDC_check("Before release lock:", mlir_read_buffer_b13(5), 0, errors);
    ACDC_check("Before release lock:", mlir_read_buffer_a33(5), 0, errors);
    ACDC_check("Before release lock:", mlir_read_buffer_b33(5), 0, errors);

    printf("Release input buffer lock.\n");
    XAieTile_LockRelease(&(TileInst[1][3]), 3, 1, 0); 

    printf("Waiting to acquire output lock for read ...\n");
    if(!XAieTile_LockAcquire(&(TileInst[3][3]), 7, 1, LOCK_TIMEOUT)) {
        printf("ERROR: timeout hit!\n");
    }

    ACDC_check("After acquire lock:", mlir_read_buffer_a13(3), 7, errors);
    ACDC_check("After acquire lock:", mlir_read_buffer_b13(5), 35, errors);
    ACDC_check("After acquire lock:", mlir_read_buffer_a33(5), 35, errors);
    ACDC_check("After acquire lock:", mlir_read_buffer_b33(5), 175, errors);

    if (!errors) {
        printf("PASS!\n"); return 0;
    } else {
        printf("Fail!\n"); return -1;
    }
    printf("test done.\n");
}