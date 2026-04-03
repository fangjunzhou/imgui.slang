struct Uniforms
{
    float4x4 proj;
    Texture2D<float4> texture;
    SamplerState sampler;
};

ConstantBuffer<Uniforms> uniforms;

struct VertexInput
{
    float2 pos : POSITION;
    float2 uv : TEXCOORD0;
    float4 col : COLOR0;
};

struct FragmentInput
{
    float2 uv;
    float4 col;
};

struct VertexOutput
{
    float4 pos : SV_Position;
    FragmentInput frag : FragmentInput;
};

[shader("vertex")]
VertexOutput vertexMain(VertexInput vIn)
{
    VertexOutput vOut;
    vOut.pos = mul(uniforms.proj, float4(vIn.pos.xy, 0.0, 1.0));
    vOut.frag.col = vIn.col;
    vOut.frag.uv = vIn.uv;
    return vOut;
}

[shader("fragment")]
float4 fragmentMain(FragmentInput pIn: FragmentInput)
    : SV_Target
{
    return pIn.col * uniforms.texture.Sample(uniforms.sampler, pIn.uv);
}
