// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0
// Adder DUT
`timescale 1ns/1ps

module adder #(
  parameter integer DATA_WIDTH = 4
) (
  input  logic unsigned [DATA_WIDTH-1:0] a,
  input  logic unsigned [DATA_WIDTH-1:0] b,
  output logic unsigned [DATA_WIDTH:0]   q
);

  assign q = a + b;

endmodule
