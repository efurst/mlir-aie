<!---//===- README.md --------------------------*- Markdown -*-===//
//
// This file is licensed under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// Copyright (C) 2022, Advanced Micro Devices, Inc.
// 
//===----------------------------------------------------------------------===//-->

# <ins>Section 6 - Larger Example Designs</ins>

There are a number of example designs available [here](../../programming_examples/) which further help explain many of the unique features of AI Engines and the NPU array in Ryzen™ AI. This section contains more complex application designs for both vision and machine learning use cases. In particular we will describe a ResNet implementation on for Ryzen™ AI.

## Vision Kernels

| Design name | Data type | Description | 
|-|-|-|
| [Vision Passthrough](../../programming_examples/vision/vision_passthrough/) | i8 | A simple pipeline with just one `passThrough` kernel. This pipeline's main purpose is to test whether the data movement works correctly to copy a greyscale image. | 
| [Color Detect](../../programming_examples/vision/color_detect/) | i32 | This multi-kernel, multi-core pipeline detects colors in an RGBA image.  | 
| [Edge Detect](../../programming_examples/vision/edge_detect/) | i32 | A mult-kernel, multi-core pipeline that detects edges in an image and overlays the detection on the original image. | 
| [Color Threshold](../../programming_examples/vision/color_threshold/) | i32 | A mult-core data-parallel implementation of color thresholding of a RGBA image. | 


## Machine Learning Designs

| Design name | Data type | Description | 
|-|-|-|
|[bottleneck](../../programming_examples/ml/bottleneck/)|ui8|A Bottleneck Residual Block is a variant of the residual block that utilises 1x1 convolutions to create a bottleneck. The use of a bottleneck reduces the number of parameters and computations.|
|[resnet](../../programming_examples/ml/resnet/)|ui8|ResNet with offloaded conv2_x bottleneck blocks. The implementation features kernel fusion and dataflow optimizations highlighting the unique architectural capabilties of AI Engines.|

-----
[[Prev - Section 5](../section-5/)] [[Top](..)]