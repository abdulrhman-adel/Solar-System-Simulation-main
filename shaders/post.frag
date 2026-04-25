#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTexture;

void main() {
    vec4 baseColor = texture(screenTexture, TexCoord);
    
    // Simple single-pass bloom using box blur
    vec4 bloomColor = vec4(0.0);
    int radius = 4;
    float offset_x = 1.0 / 800.0;
    float offset_y = 1.0 / 600.0;
    
    int count = 0;
    for(int x = -radius; x <= radius; x++) {
        for(int y = -radius; y <= radius; y++) {
            vec2 sample_pos = TexCoord + vec2(x * offset_x, y * offset_y);
            vec4 col = texture(screenTexture, sample_pos);
            
            // Brightness threshold
            float brightness = max(max(col.r, col.g), col.b);
            if(brightness > 0.95) {
                bloomColor += col;
            }
            count++;
        }
    }
    
    bloomColor /= float(count);
    
    // Additive blending 
    // Emphasize the bloom to make the sun look extremely bright
    FragColor = baseColor + bloomColor * 1.5;
}
