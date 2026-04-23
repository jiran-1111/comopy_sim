
`timescale 1ns / 1ps
module Andgate (
    input  a,
    input  b,
    output out
);
    assign out = a & b;
endmodule

module SimpleAdder (
    input  [4:0] a,
    input  [4:0] b,
    output [4:0] q
);
    assign q = a + b;
endmodule

module add16 (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout
);
    wire [16:0] full_res;

    assign full_res = {1'b0, a} + {1'b0, b} + {16'b0, cin};
    assign sum  = full_res[15:0];
    assign cout = full_res[16];
endmodule

module Module_add (
    input  [31:0] a,
    input  [31:0] b,
    output [31:0] sum
);
    wire        carry_internal;

    add16 lo (
        .a(a[15:0]),
        .b(b[15:0]),
        .cin(1'b0),
        .sum(sum[15:0]),
        .cout(carry_internal)
    );

    add16 hi (
        .a(a[31:16]),
        .b(b[31:16]),
        .cin(carry_internal),
        .sum(sum[31:16]),
        .cout() // 最高位进位悬空
    );
endmodule

module Reduction (
    input  [7:0] in_,
    output       parity
);
    assign parity = ^in_; // 缩减异或运算
endmodule

module Always_casez (
    input  [7:0] in_,
    output reg [2:0] pos
);
    always @(*) begin
        casez (in_)
            8'b???????1: pos = 3'd0;
            8'b??????10: pos = 3'd1;
            8'b?????100: pos = 3'd2;
            8'b????1000: pos = 3'd3;
            8'b???10000: pos = 3'd4;
            8'b??100000: pos = 3'd5;
            8'b?1000000: pos = 3'd6;
            8'b10000000: pos = 3'd7;
            default:     pos = 3'd0;
        endcase
    end
endmodule

module SimpleReg (
    input        clk,
    input  [7:0] d,
    output reg [7:0] q
);
    always @(posedge clk) begin
        q <= d;
    end
endmodule

module Adder (
    input        clk,
    input  [4:0] a,
    input  [4:0] b,
    output [4:0] q,
    output reg [4:0] q_ff
);
    // 组合逻辑输出
    assign q = a + b;

    // 时序逻辑输出
    always @(posedge clk) begin
        q_ff <= a + b;
    end
endmodule

module Module_shift8 (
    input        clk, // Module 默认包含 clk
    input  [7:0] d,
    input  [1:0] sel,
    output reg [7:0] q
);
    reg [7:0] q0, q1, q2;

    // 实例化三个D触发器（简化为always块描述）
    always @(posedge clk) begin
        q0 <= d;
        q1 <= q0;
        q2 <= q1;
    end

    // 选择逻辑
    always @(*) begin
        case (sel)
            2'd0: q = d;
            2'd1: q = q0;
            2'd2: q = q1;
            2'd3: q = q2;
            default: q = d;
        endcase
    end
endmodule

module Module_shift (
    input  clk,
    input  d,
    output q
);
    wire a, b;

    // 级联连接，这里 my_dff 内部仅为 assign q = d
    assign a = d;
    assign b = a;
    assign q = b;
endmodule