#include "gen_cdo.h"
#include <cstring>
#include <iostream>
/********************************************* Disclaimer
 * *********************************************/
/* This file is generated by aie-translate. */
/* Changes to this file may cause incorrect behavior. */

/************************** Constants/Macros *****************************/
#define HW_GEN XAIE_DEV_GEN_AIEML
#define XAIE_NUM_ROWS 6
#define XAIE_NUM_COLS 5
#define XAIE_BASE_ADDR 0x40000000
#define XAIE_COL_SHIFT 25
#define XAIE_ROW_SHIFT 20
#define XAIE_SHIM_ROW 0
#define XAIE_MEM_TILE_ROW_START 1
#define XAIE_MEM_TILE_NUM_ROWS 1
#define XAIE_AIE_TILE_ROW_START 2
#define XAIE_AIE_TILE_NUM_ROWS 4
#define FOR_WRITE 0
#define FOR_READ 1
#define XAIE_PARTITION_BASE_ADDR 0x0

/***************************** Includes *********************************/
#include <xaiengine.h>

#define __mlir_aie_try(x) x
static XAie_DmaDimDesc *__mlir_aie_alloc_dim_desc(size_t ndims) {
  XAie_DmaDimDesc *ret = NULL;
  ret = (XAie_DmaDimDesc *)calloc(sizeof(XAie_DmaDimDesc), ndims);
  if (NULL == ret) {
    fprintf(stderr, "Allocating DmaDimDesc failed.\n");
  }
  return ret;
}
XAie_InstDeclare(DevInst, &ConfigPtr); // Declare global device instance

bool ppgraph_load_elf(const std::string &work_path,
                      std::vector<std::string> &elfInfoPath) {
  std::string work_dir = (work_path.empty() ? "Work" : work_path);
  {
    if (XAie_LoadElf(&DevInst, XAie_TileLoc(0, 2),
                     (work_dir + "/core_0_2.elf").c_str(),
                     XAIE_ENABLE) != XAIE_OK) {
      std::cerr << "ERROR: Failed to load elf for core(%d,%d)" << std::endl;
      return false;
    }
  }
  return true;
} // ppgraph_load_elf

void ppgraph_core_enable() {
  XAie_CoreEnable(&DevInst, XAie_TileLoc(0, 2));
  return;
} // ppgraph_core_enable

void enableErrorHandling() {
  XAie_ErrorHandlingInit(&DevInst);
} // enableErrorHandling

void ppgraph_init(const std::string &work_path) {
  XAie_CoreReset(&DevInst, XAie_TileLoc(0, 2));
  XAie_CoreUnreset(&DevInst, XAie_TileLoc(0, 2));
  for (int l = 0; l < 16; l++)
    XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 2), XAie_LockInit(l, 0));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 0), XAie_LockInit(2, 0));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 0), XAie_LockInit(3, 0));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 2), XAie_LockInit(0, 2));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 2), XAie_LockInit(1, 0));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 0), XAie_LockInit(0, 0));
  XAie_LockSetValue(&DevInst, XAie_TileLoc(0, 0), XAie_LockInit(1, 0));

  XAie_DmaDesc dma_tile02_bd0;
  XAie_DmaDescInit(&DevInst, &(dma_tile02_bd0), XAie_TileLoc(0, 2));
  XAie_DmaSetLock(&(dma_tile02_bd0), XAie_LockInit(0, -1), XAie_LockInit(1, 1));
  XAie_DmaSetAddrLen(&(dma_tile02_bd0), /* addrA */ 0x400, /* len */ 1024 * 4);
  XAie_DmaSetNextBd(&(dma_tile02_bd0), /* nextbd */ 1, /* enableNextBd */ 1);
  XAie_DmaEnableBd(&(dma_tile02_bd0));
  XAie_DmaWriteBd(&DevInst, &(dma_tile02_bd0), XAie_TileLoc(0, 2), /* bd */ 0);

  XAie_DmaDesc dma_tile02_bd1;
  XAie_DmaDescInit(&DevInst, &(dma_tile02_bd1), XAie_TileLoc(0, 2));
  XAie_DmaSetLock(&(dma_tile02_bd1), XAie_LockInit(0, -1), XAie_LockInit(1, 1));
  XAie_DmaSetAddrLen(&(dma_tile02_bd1), /* addrA */ 0x1400, /* len */ 1024 * 4);
  XAie_DmaSetNextBd(&(dma_tile02_bd1), /* nextbd */ 0, /* enableNextBd */ 1);
  XAie_DmaEnableBd(&(dma_tile02_bd1));
  XAie_DmaWriteBd(&DevInst, &(dma_tile02_bd1), XAie_TileLoc(0, 2), /* bd */ 1);

  XAie_DmaDesc dma_tile02_bd2;
  XAie_DmaDescInit(&DevInst, &(dma_tile02_bd2), XAie_TileLoc(0, 2));
  XAie_DmaSetLock(&(dma_tile02_bd2), XAie_LockInit(1, -1), XAie_LockInit(0, 1));
  XAie_DmaSetAddrLen(&(dma_tile02_bd2), /* addrA */ 0x400, /* len */ 1024 * 4);
  XAie_DmaSetNextBd(&(dma_tile02_bd2), /* nextbd */ 3, /* enableNextBd */ 1);
  XAie_DmaEnableBd(&(dma_tile02_bd2));
  XAie_DmaWriteBd(&DevInst, &(dma_tile02_bd2), XAie_TileLoc(0, 2), /* bd */ 2);

  XAie_DmaDesc dma_tile02_bd3;
  XAie_DmaDescInit(&DevInst, &(dma_tile02_bd3), XAie_TileLoc(0, 2));
  XAie_DmaSetLock(&(dma_tile02_bd3), XAie_LockInit(1, -1), XAie_LockInit(0, 1));
  XAie_DmaSetAddrLen(&(dma_tile02_bd3), /* addrA */ 0x1400, /* len */ 1024 * 4);
  XAie_DmaSetNextBd(&(dma_tile02_bd3), /* nextbd */ 2, /* enableNextBd */ 1);
  XAie_DmaEnableBd(&(dma_tile02_bd3));
  XAie_DmaWriteBd(&DevInst, &(dma_tile02_bd3), XAie_TileLoc(0, 2), /* bd */ 3);

  XAie_DmaChannelPushBdToQueue(&DevInst, XAie_TileLoc(0, 2), /* ChNum */ 0,
                               /* dmaDir */ DMA_S2MM, /* BdNum */ 0);
  XAie_DmaChannelEnable(&DevInst, XAie_TileLoc(0, 2), /* ChNum */ 0,
                        /* dmaDir */ DMA_S2MM);
  XAie_DmaChannelPushBdToQueue(&DevInst, XAie_TileLoc(0, 2), /* ChNum */ 0,
                               /* dmaDir */ DMA_MM2S, /* BdNum */ 2);
  XAie_DmaChannelEnable(&DevInst, XAie_TileLoc(0, 2), /* ChNum */ 0,
                        /* dmaDir */ DMA_MM2S);
  int x, y;
  // Core Stream Switch column 0 row 0
  x = 0;
  y = 0;
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), CTRL, 0, SOUTH, 0);
  {
    // configure DMA_<S2MM/MM2S>_<N>_Ctrl register
    XAie_DmaChannelDesc DmaChannelDescInst;
    XAie_DmaChannelDescInit(&DevInst, &DmaChannelDescInst, XAie_TileLoc(x, y));
    XAie_DmaChannelSetControllerId(&DmaChannelDescInst, 0);
    XAie_DmaWriteChannel(&DevInst, &DmaChannelDescInst, XAie_TileLoc(x, y), 0,
                         DMA_S2MM);
  }

  {
    // configure DMA_<S2MM/MM2S>_<N>_Ctrl register
    XAie_DmaChannelDesc DmaChannelDescInst;
    XAie_DmaChannelDescInit(&DevInst, &DmaChannelDescInst, XAie_TileLoc(x, y));
    XAie_DmaChannelSetControllerId(&DmaChannelDescInst, 0);
    XAie_DmaWriteChannel(&DevInst, &DmaChannelDescInst, XAie_TileLoc(x, y), 1,
                         DMA_S2MM);
  }

  XAie_AieToPlIntfEnable(&DevInst, XAie_TileLoc(x, y), 0, PLIF_WIDTH_32);
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), SOUTH, 3, NORTH, 0);
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), NORTH, 0, SOUTH, 2);
  // Core Stream Switch column 0 row 2
  x = 0;
  y = 2;
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), SOUTH, 0, DMA, 0);
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), DMA, 0, SOUTH, 0);
  // Core Stream Switch column 0 row 1
  x = 0;
  y = 1;
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), SOUTH, 0, NORTH, 0);
  XAie_StrmConnCctEnable(&DevInst, XAie_TileLoc(x, y), NORTH, 0, SOUTH, 0);
  // ShimMux column 0 row 0
  // NOTE ShimMux always connects from the south as directions are defined
  // relative to the tile stream switch
  x = 0;
  y = 0;
  XAie_EnableShimDmaToAieStrmPort(&DevInst, XAie_TileLoc(x, y), 3);
  XAie_EnableAieToShimDmaStrmPort(&DevInst, XAie_TileLoc(x, y), 2);
} // ppgraph_init

class InitializeAIEControl {
public:
  InitializeAIEControl() {
    XAie_SetupConfig(ConfigPtr, HW_GEN, XAIE_BASE_ADDR, XAIE_COL_SHIFT,
                     XAIE_ROW_SHIFT, XAIE_NUM_COLS, XAIE_NUM_ROWS,
                     XAIE_SHIM_ROW, XAIE_MEM_TILE_ROW_START,
                     XAIE_MEM_TILE_NUM_ROWS, XAIE_AIE_TILE_ROW_START,
                     XAIE_AIE_TILE_NUM_ROWS);

    XAie_SetupPartitionConfig(&DevInst, XAIE_PARTITION_BASE_ADDR, 1, 1);

    XAie_CfgInitialize(&(DevInst), &ConfigPtr);

#if defined(__AIESIM__)
#if defined(__CDO__)
    XAie_SetIOBackend(
        &(DevInst),
        XAIE_IO_BACKEND_CDO); // Set aiengine driver library to run for CDO Mode
    XAie_UpdateNpiAddr(&(DevInst), 0x0);
#else
    // AIE driver currently error out XAie_UpdateNpiAddr for AIESIM
#endif
#else
    XAie_UpdateNpiAddr(&(DevInst), 0x0);
#endif

#if defined(__AIESIM__) && !defined(__CDO__)
    XAie_TurnEccOff(&DevInst);
#endif

#if defined(__AIESIM__) && !defined(__CDO__)
    extern unsigned ess_debug;
#else
    unsigned ess_debug = false;
#endif

#ifdef __EXCLUDE_PL_CONTROL__
    bool exclude_pl_control = true;
#else
    bool exclude_pl_control = false;
#endif

#ifdef __CDO__
    int trace_config_stream_option = 2;
#else
    int trace_config_stream_option = 0;
#endif
  }
} initAIEControl;

extern "C" {
#include "cdo_driver.h"
}

void initializeCDOGenerator(bool AXIdebug, bool endianness) {
  if (AXIdebug)
    EnAXIdebug(); // Enables AXI-MM prints for configs being added in CDO,
                  // helpful for debugging
  setEndianness(endianness);
}

void addInitConfigToCDO(const std::string &workDirPath) {
  ppgraph_init(workDirPath);
}

void addCoreEnableToCDO() { ppgraph_core_enable(); }

void addErrorHandlingToCDO() { enableErrorHandling(); }

void addAieElfsToCDO(const std::string &workDirPath) {
  std::vector<std::string> elfInfoPath;
  if (!ppgraph_load_elf(workDirPath, elfInfoPath))
    exit(EXIT_FAILURE);
}

void generateCDOBinariesSeparately(const std::string &workDirPath,
                                   bool AXIdebug) {

  // aie_cdo_error_handling.bin
  const std::string errorHandlingCDOFilePath =
      workDirPath + "aie_cdo_error_handling.bin";
  if (AXIdebug)
    std::cout << "START: Error Handling Configuration\n";
  startCDOFileStream(errorHandlingCDOFilePath.c_str());
  FileHeader();
  addErrorHandlingToCDO();
  configureHeader();
  endCurrentCDOFileStream();
  if (AXIdebug)
    std::cout << "DONE: Error Handling Configuration\n\n";

  // aie_cdo_elfs.bin
  const std::string elfsCDOFilePath = workDirPath + "aie_cdo_elfs.bin";
  if (AXIdebug)
    std::cout << "START: AIE ELF Configuration\n";
  startCDOFileStream(elfsCDOFilePath.c_str());
  FileHeader();
  addAieElfsToCDO(workDirPath);
  configureHeader();
  endCurrentCDOFileStream();
  if (AXIdebug)
    std::cout << "DONE: AIE ELF Configuration\n\n";

  // aie_cdo_init.bin
  const std::string initCfgCDOFilePath = workDirPath + "aie_cdo_init.bin";
  if (AXIdebug)
    std::cout << "START: Initial Configuration (SHIM and AIE Array)\n";
  startCDOFileStream(initCfgCDOFilePath.c_str());
  FileHeader();
  addInitConfigToCDO(workDirPath);
  configureHeader();
  endCurrentCDOFileStream();
  if (AXIdebug)
    std::cout << "DONE: Initial Configuration (SHIM and AIE Array)\n\n";

  // aie_cdo_enable.bin
  const std::string coreEnableCDOFilePath = workDirPath + "aie_cdo_enable.bin";
  if (AXIdebug)
    std::cout << "START: Core Enable Configuration\n";
  startCDOFileStream(coreEnableCDOFilePath.c_str());
  FileHeader();
  addCoreEnableToCDO();
  configureHeader();
  endCurrentCDOFileStream();
  if (AXIdebug)
    std::cout << "DONE: Core Enable Configuration\n\n";
}
