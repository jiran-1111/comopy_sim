`timescale 1ns/1ps
module adder (
    input wire clk,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output wire [4:0] q
);

assign q = a + b;

endmodule