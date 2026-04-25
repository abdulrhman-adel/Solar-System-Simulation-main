#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D textTexture;

void main() {
    vec4 texColor = texture(textTexture, TexCoord);
    // Discard completely transparent pixels so they bypass blending/depth completely
    if (texColor.a < 0.05) discard;
    FragColor = texColor;
}
