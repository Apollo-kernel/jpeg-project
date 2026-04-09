# FPGA-Based JPEG-LS Regular-Mode Encoder

## a. GitHub Repo

**Repository URL:**  
`https://github.com/Apollo-kernel/jpeg-project`

---

## b. Project Team

- `Jiarun Qiu`
- `Cheng Cheng`
- `Yuyang Huang` 

---

## c. IP Definition

### 1. What the IP does

This project designs a custom FPGA IP block for **lossless grayscale image compression based on the regular-mode path of JPEG-LS**.

The IP takes an input grayscale image and produces a compressed output bitstream.  

To keep the project scope manageable for the class timeline, the first implementation will support:

- 8-bit grayscale images
- encoder only
- lossless mode
- regular mode only

Run mode is intentionally excluded from the initial implementation due to its higher hardware complexity. This allows the team to focus on building a correct, modular, and verifiable hardware architecture.

### 2. Why this IP is a good hardware project

This IP is a good fit for hardware acceleration because the computation is highly local and structured.  
Each output code depends mainly on the current pixel and a small causal neighborhood from nearby pixels.  
This makes the design suitable for line buffers, streaming datapaths, pipelining, and modular decomposition.

The project also fits the class requirements well because it has:

- a clearly defined hardware/software boundary
- a well-scoped accelerator function
- measurable outputs such as correctness, compression ratio, latency, and resource usage
- a natural testbench strategy based on comparison to a software reference model

### 3. Inputs and outputs

#### Inputs
- grayscale image pixel stream (8-bit per pixel)
- image width and height
- start signal and configuration parameters (via control registers)
- (optional) Input/output base addresses when integrated with a shared memory system

#### Outputs
- compressed output bitstream (or packed encoded words)
- done status signal indicating completion of the compression process

### 4. Mathematical operations performed in the IP

The IP performs the following core operations for each pixel in raster scan order.

#### a. Causal neighborhood extraction
For the current pixel `x`, the encoder uses nearby causal pixels:
- `A` = left
- `B` = upper
- `C` = upper-left
- `D` = upper-right

#### b. Local gradient calculation
The encoder computes local gradients such as:

- `g1 = D - B`
- `g2 = B - C`
- `g3 = C - A`

These gradients characterize the local image structure and are used for context selection.

#### c. Context quantization
The gradients are quantized into a finite set of context bins.  
This converts raw local structure into a smaller context index that can be used by the entropy coding stage.

#### d. Prediction
The encoder computes a predictor for the current pixel using a median edge detector style rule.  
A simplified pseudocode form is:

```python
if C >= max(A, B):
    Px = min(A, B)
elif C <= min(A, B):
    Px = max(A, B)
else:
    Px = A + B - C
```

#### e. Prediction residual
The prediction error is:

```python
Err = x - Px
```

#### f. Error mapping
The signed prediction error is mapped into a nonnegative integer domain so it can be entropy coded efficiently.

A simplified example is:

```python
if Err >= 0:
    MErr = 2 * Err
else:
    MErr = -2 * Err - 1
```

#### g. Adaptive code selection and coding
The mapped error is encoded using a Golomb-style variable-length code selected from lightweight adaptive statistics.

#### h. Bit packing
The variable-length codes are packed into output words and written to memory or streamed out.

### 5. Why these operations are well-suited for hardware acceleration

These operations are well-suited for FPGA acceleration because:

- they use mostly integer arithmetic
- they rely on small local neighborhoods rather than global image transforms
- they can be decomposed into pipeline stages
- they support streaming execution with predictable data movement
- line buffers can efficiently provide the required neighboring pixels
- the control and datapath are regular enough for modular HLS implementation

---

## d. IP Architecture

### 1. Overall system view

The system consists of a host processor (PS) and a custom JPEG-LS encoder IP in programmable logic.

The host processor is responsible for:
- loading the input image into memory
- programming control registers
- launching the accelerator
- reading the compressed output and metadata

The custom IP is responsible for:
- reading image data
- generating local neighborhoods
- computing prediction and context information
- encoding prediction errors
- packing the compressed output
- reporting completion and output size

### 2. Interface choice

The initial design will use:

- **AXI4-Lite** for control and status registers
- **AXI4 memory-mapped (`m_axi`)** for reading input image data from shared memory and writing compressed output back to shared memory

A possible later extension is to replace or supplement memory-mapped pixel transfer with **AXI4-Stream** for a more purely streaming pipeline.

### 3. Major hardware modules

#### Module 1: Control and Register Interface
This module exposes control/status registers to the PS through AXI4-Lite.  
Registers include image width, image height, input address, output address, start, done, and output byte count.

#### Module 2: Input Reader
This module reads image pixels from external memory through an `m_axi` interface.  
It outputs pixels in raster order into the internal processing pipeline.

#### Module 3: Line Buffer / Neighborhood Generator
This module stores enough prior row information to generate the causal neighborhood `(A, B, C, D)` for each current pixel.  
It is essential for turning a raw pixel stream into context for prediction.

#### Module 4: Gradient and Context Module
This module computes local gradients and quantizes them into a context index.  
It converts neighborhood structure into a compact coding context for the later entropy stage.

#### Module 5: Predictor Module
This module computes the predicted pixel value using a median-based edge-aware predictor.  
Its output is the prediction used to form the residual.

#### Module 6: Residual and Mapping Module
This module subtracts the predictor from the current pixel to compute the prediction error, then maps the signed error into a nonnegative integer form for entropy coding.

#### Module 7: Entropy Coding Module
This module performs adaptive Golomb-style coding of the mapped residual.  
It produces variable-length codewords and updates lightweight coding statistics.

#### Module 8: Bit Packer / Output Writer
This module packs variable-length codewords into aligned output words.  
It writes packed output data back to memory and tracks the total output size.

### 4. Internal communication between modules

The modules will communicate through a staged streaming datapath inside the IP.  
Conceptually, the dataflow is:

```text
Input Reader
-> Line Buffer / Neighborhood Generator
-> Gradient and Context Module
-> Predictor Module
-> Residual and Mapping Module
-> Entropy Coding Module
-> Bit Packer / Output Writer
```

This decomposition avoids one monolithic module and makes the design easier to test incrementally.

### 5. Why this modularization is useful

This modular structure helps the project in several ways:

- each stage can be unit-tested independently
- the team can develop modules in parallel
- the architecture naturally supports pipelining
- debugging is easier because intermediate values can be checked against a software model
- the design can later be extended with run mode or a decoder without rewriting the entire system

---

## Initial Verification Plan

Although the detailed verification strategy will be described in `detailed_plan.md`, the initial plan is:

- build a small Python reference model for grayscale regular-mode encoding
- test on tiny synthetic images first
- compare intermediate values such as predictor, residual, mapped residual, and output words
- then test on larger images
- report correctness, output size, latency estimates, and synthesis resource usage

Planned test image categories:
- all-zero image
- constant image
- horizontal gradient
- vertical gradient
- checkerboard pattern
- random image
- small corner-case sizes such as `1xN`, `Nx1`, `4x4`, and `8x8`

---

## Expected Deliverables

The repository is expected to contain:

- `initial_plan.md`
- `detailed_plan.md`
- Vitis HLS source code
- HLS testbench
- Python reference model
- simulation outputs
- synthesis reports
- result summary and discussion

---

## Stretch Goals

If the base design is completed early, the team may explore one or more of the following:

- adding JPEG-LS run mode
- supporting near-lossless mode
- supporting 16-bit grayscale images
- adding an AXI4-Stream front-end
- measuring throughput in cycles per pixel
- comparing compression ratio and runtime against a software baseline

---

## Summary

We propose a custom Vitis HLS IP for grayscale lossless image compression using the regular-mode path of JPEG-LS.  
The project is intentionally scoped to a modular, testable encoder-only design with AXI-based PS/IP integration.  
The design focuses on local prediction, context modeling, adaptive entropy coding, and efficient bit packing, all of which are good candidates for FPGA acceleration.
