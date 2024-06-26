##===- Makefile -----------------------------------------------------------===##
# 
# This file licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# 
##===----------------------------------------------------------------------===##

srcdir := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

include ${srcdir}/../../makefile-common

targetname = vectorAdd
devicename = npu
col = 0

all: build/final.xclbin

build/aie.mlir: ${srcdir}/aie2.py
	mkdir -p ${@D}
	python3 $< ${devicename} ${col} > $@

build/final.xclbin: build/aie.mlir
	mkdir -p ${@D}
	cd ${@D} && aiecc.py --aie-generate-cdo --aie-generate-npu --no-compile-host \
		--xclbin-name=${@F} --npu-insts-name=insts.txt ${<F}

${targetname}.exe: ${srcdir}/test.cpp
	rm -rf _build
	mkdir -p _build
	cd _build && ${powershell} cmake ${srcdir} -DTARGET_NAME=${targetname}
	cd _build && ${powershell} cmake --build . --config Release
ifeq "${powershell}" "powershell.exe"
	cp _build/${targetname}.exe $@
else
	cp _build/${targetname} $@ 
endif

# Changing variables when we target VCK5000
ACDC_AIE = $(dir $(shell which aie-opt))/..

vck5000: devicename=xcvc1902
vck5000: col=6

vck5000: build/aie.mlir
	aiecc.py --xchesscc --link_against_hsa --host-target=x86_64-amd-linux-gnu build/aie.mlir \
						-I/opt/xaiengine/include \
						-I$(ACDC_AIE)/runtime_lib/x86_64-hsa/test_lib/include \
            -I${ROCM_ROOT}/include \
						-L/opt/xaiengine/lib \
            -L/lib/x86_64-linux-gnu/ \
						test_vck5000.cpp \
						$(ACDC_AIE)/runtime_lib/x86_64-hsa/test_lib/src/test_library.cpp \
            ${ROCM_ROOT}/lib/libhsa-runtime64.so.1.9.0 \
						-Wl,-R/opt/xaiengine/lib \
            -Wl,-rpath,${ROCM_ROOT}/lib \
						-Wl,--whole-archive -Wl,--no-whole-archive -lstdc++ -ldl -lelf -o test.elf

run: ${targetname}.exe build/final.xclbin build/insts.txt 
	${powershell} ./$< -x build/final.xclbin -i build/insts.txt -k MLIR_AIE

clean:
	rm -rf build _build inst aie.mlir.prj core_* test.elf ${targetname}.exe
