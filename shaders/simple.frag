#version 330 core

#define NUM_LIGHTS 2

// Input variables
in vec2 DiffuseTexCoord;
in vec2 NormalTexCoord;
in vec2 CloudTexCoord;
in vec3 Normal;
in vec3 FragPos;
in vec3 VertexPos;
in vec3 LightPositions[NUM_LIGHTS];

// Output variable
out vec4 FragColor;

// Uniform variables
uniform sampler2D diffuseTexture;
uniform sampler2D normalTexture;
uniform sampler2D cloudTexture;
uniform float cloudAnimationTime;
uniform bool isEarth;
uniform bool isOrbit;
uniform vec3 sunPosition;
uniform float sunRadius;
uniform vec3 sunColor;
uniform vec3 viewPos;
uniform vec3 ka;
uniform vec3 kd;
uniform vec3 ks;
uniform float shininess;
uniform bool isSun;
uniform float atmosphereThickness;
uniform vec3 atmosphereColor;
uniform bool isStarryBackground;
uniform vec3 lightColors[NUM_LIGHTS];
uniform vec3 lightPositions[NUM_LIGHTS];
uniform float lightRadii[NUM_LIGHTS];

void main() {
    if (isOrbit) {
        FragColor = vec4(1.0, 1.0, 1.0, 0.4); // White semi-transparent orbit line
        return;
    }

    // Sample the diffuse and normal textures
    vec4 diffuseColor = texture(diffuseTexture, DiffuseTexCoord);
    vec3 normal = texture(normalTexture, NormalTexCoord).rgb;
    normal = normalize(normal);

    if (isSun) {
        // Sun: Always fully illuminated
        FragColor = diffuseColor;
    } else if (isStarryBackground) {
        // Starry background: Always fully illuminated
        FragColor = diffuseColor;
    } else {
        // Planets: Apply lighting calculations
        vec3 norm = normalize(Normal);
        norm = normalize(norm + normal);

        vec3 viewDir = normalize(viewPos - FragPos);

        vec3 result = vec3(0.0);

        vec3 current_ks = ks;
        if (isEarth) {
            vec4 baseEarth = texture(diffuseTexture, DiffuseTexCoord);
            if (baseEarth.b > baseEarth.r * 1.5) {
                current_ks = vec3(0.8, 0.8, 0.8); // Ocean
            } else {
                current_ks = vec3(0.05, 0.05, 0.05); // Land
            }
        }

        // Sun lighting with attenuation
        float sunDistance = length(sunPosition - FragPos);
        vec3 lightDir = normalize(sunPosition - FragPos);
        float NdotL = max(dot(norm, lightDir), 0.0);
        float NdotL_raw = dot(norm, lightDir); // Raw dot for city lights terminator
        
        vec3 diffuse = kd * NdotL * sunColor;
        vec3 halfDir = normalize(lightDir + viewDir);
        float NdotH = max(dot(norm, halfDir), 0.0);
        vec3 specular = current_ks * pow(NdotH, shininess) * sunColor;
        float sunAttenuation = 1.0 / (1.0 + 0.01 * sunDistance + 0.001 * sunDistance * sunDistance);
        result += (diffuse + specular) * sunAttenuation;

        // Emissive planets lighting
        for (int i = 0; i < NUM_LIGHTS; i++) {
            // Calculate the distance from the fragment to the light source
            float distance = length(lightPositions[i] - FragPos);

            // Ambient lighting
            vec3 ambient = ka;

            // Diffuse lighting
            vec3 lightDir = normalize(lightPositions[i] - FragPos);
            float NdotL = max(dot(norm, lightDir), 0.0);
            vec3 diffuse = kd * NdotL;

            // Specular lighting
            vec3 halfDir = normalize(lightDir + viewDir);
            float NdotH = max(dot(norm, halfDir), 0.0);
            vec3 specular = current_ks * pow(NdotH, shininess);

            // Attenuation based on distance
            float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);

            // Increase the intensity of the emissive planets
            float emissiveIntensity = 0.5;

            // Combine the lighting components
            result += (ambient + diffuse + specular) * lightColors[i] * attenuation * emissiveIntensity;
        }

        if (isEarth) {
            // Apply cloud texture for Earth
            vec2 animatedCloudTexCoord = CloudTexCoord + vec2(cloudAnimationTime, 0.0);
            vec4 cloudColor = texture(cloudTexture, animatedCloudTexCoord);
            
            // Blend the cloud color with the diffuse color based on the cloud alpha
            float cloudAlpha = 0.5; // Adjust this value to control the transparency of the clouds
            diffuseColor.rgb = mix(diffuseColor.rgb, cloudColor.rgb, cloudColor.a * cloudAlpha);
        }

        // Apply the lighting to the diffuse color
        vec3 finalColor = result * diffuseColor.rgb;

        if (isEarth) {
            vec4 baseEarth = texture(diffuseTexture, DiffuseTexCoord);
            bool isLand = (baseEarth.g > baseEarth.b) || (baseEarth.r > baseEarth.b * 0.8);
            if (isLand && NdotL_raw < 0.1) {
                float scale = 200.0;
                vec2 p = DiffuseTexCoord * scale;
                float noise = fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
                
                // Clusters to simulate cities
                float mask = smoothstep(0.85, 1.0, noise);
                
                // Fade lights in near the terminator
                float fade = smoothstep(0.1, -0.2, NdotL_raw);
                
                // Add a warm yellow-ish city light glow
                finalColor += vec3(1.0, 0.8, 0.4) * mask * fade * 0.8;
            }
        }

        // Gamma correction
        const float gamma = 2.2;
        vec3 gammaCorrectedColor = pow(finalColor, vec3(1.0 / gamma));

        // Output the final color
        FragColor = vec4(gammaCorrectedColor, diffuseColor.a);
    }
}