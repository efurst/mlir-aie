##===- Makefile -----------------------------------------------------------===##
# 
# This file licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# 
##===----------------------------------------------------------------------===##

srcdir := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

include ${srcdir}/../../makefile-common

ACDC_AIE = $(dir $(shell which aie-opt))/..

targetname = reduce_add
devicename = npu
col = 0
CHESS_FLAGS=${CHESSCCWRAP2_FLAGS}

all: build/final.xclbin build/insts.txt

VPATH := ${srcdir}/../../../aie_kernels/aie2

build/%.cc.o: %.cc
	mkdir -p ${@D}
	cd ${@D} && xchesscc_wrapper ${CHESSCCWRAP2_FLAGS} -c $< -o ${@F}

build/aie.mlir: ${srcdir}/aie2.py
	mkdir -p ${@D}
	python3 $< ${devicename} ${col} > $@

build/final.xclbin: build/aie.mlir build/reduce_add.cc.o
	mkdir -p ${@D}
	cd ${@D} && aiecc.py --aie-generate-cdo --no-compile-host --xclbin-name=${@F} \
				--aie-generate-npu --npu-insts-name=insts.txt $(<:%=../%)

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

run: ${targetname}.exe build/final.xclbin build/insts.txt 
	${powershell} ./$< -x build/final.xclbin -i build/insts.txt -k MLIR_AIE

trace:
	../../utils/parse_eventIR.py --filename trace.txt --mlir build/aie.mlir --colshift 1 > parse_eventIR_vs.json

clean_trace:
	rm -rf tmpTrace trace.txt

# Changing variables when we target VCK5000
vck5000: devicename=xcvc1902
vck5000: col=6
vck5000: CHESS_FLAGS=${CHESSCCWRAP1_FLAGS}
vck5000: KERNEL_LIB=${ACDC_AIE}/../aie_kernels/aie1/

vck5000: build/aie.mlir build/scale.o
	cp build/scale.o* ./
	aiecc.py --link_against_hsa --host-target=x86_64-amd-linux-gnu build/aie.mlir \
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

clean: clean_trace
	rm -rf build _build inst aie.mlir.prj core_* test.elf ${targetname}.exe
