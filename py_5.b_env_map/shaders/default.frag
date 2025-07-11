#version 460 core

layout (location = 0) out vec4 frag_color;

in vec2 uv_0;
in vec3 normal;
in vec4 frag_world_pos;
in vec4 shadow_coord;

struct Light {
  vec3 position;
  vec3 direction;
  vec3 color;
  float strength;
};

struct PointLight {
  vec3 position;
  vec3 color;
  float strength;
};

struct SpotLight {
  vec3 position;
  vec3 direction;
  vec3 color;
  float strength;
  float cutoff;
  float softness;
};

struct Material {
  vec3 a;
  float d;
  float s;
  float r;
};

const int max_lights = 99;

// uniform vec2 u_resolution;
uniform vec3 cam_pos;
uniform PointLight lights[max_lights];
uniform float num_lights;

uniform Light global_light;
uniform SpotLight flash_light;

uniform float texture_blend;
uniform float local_light_blend;
uniform Material material;
uniform Material skybox_material;
uniform sampler2D u_tex_albedo;
uniform sampler2DShadow shadow_map_tex;

uniform samplerCube u_cube_map;

const float PI = 3.14159265359;
const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

// const vec3 fog_albedo = vec3(0.333);
// const float fog_scale = 0.15 / 10; // Higher is stronger rescale [0.0 to 1.0] to [0.0 to 0.1] i.e 0.015;

/* Percentage-closer filtering, softens the shadow edges */
// float lookup(float ox, float oy) {
//   vec2 pixelOffset = 1 / u_resolution;
//   return textureProj(shadow_map_tex, shadow_coord + vec4(ox * pixelOffset.x * shadow_coord.w, oy * pixelOffset.y * shadow_coord.w, 0.0, 0.0));
// }
// float get_shadow_pcf_4() {
//   float shadow;
//   const float spread = 1.5;  // shadow spread
//   const vec2 offset = mod(floor(gl_FragCoord.xy), 2.0) * spread;
//   shadow += lookup(-1.5 * spread + offset.x, 1.5 * spread - offset.y);
//   shadow += lookup(-1.5 * spread + offset.x, -0.5 * spread - offset.y);
//   shadow += lookup(0.5 * spread + offset.x, 1.5 * spread - offset.y);
//   shadow += lookup(0.5 * spread + offset.x, -0.5 * spread - offset.y);
//   return shadow * 0.25;
// }
// float get_shadow_pcf_16() {
//   float shadow;
//   const float spread = 1.0;
//   const float end_p = spread * 1.5;
//   for (float y = -end_p; y <= end_p; y += spread) {
//     for (float x = -end_p; x <= end_p; x += spread) {
//       shadow += lookup(x, y);
//     }
//   }
//   return shadow * 0.0625;
// }

vec3 fresnelSchlick(float cosTheta, vec3 F0) {
  return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}
float DistributionGGX(vec3 N, vec3 H, float roughness) {
  const float a2 = pow(roughness, 4.0);
  const float n_dot_h = pow(max(dot(N, H), 0.0), 2.0);
  return a2 / (pow(n_dot_h * (a2 - 1.0) + 1.0, 2.0) * PI);
}
float GeometrySchlickGGX(float n_dot_v, float roughness) {
  const float k = pow(roughness + 1.0, 2.0) / 8.0;
  return n_dot_v / (n_dot_v * (1.0 - k) + k);
}
float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
  const float ggx2 = GeometrySchlickGGX(max(dot(N, V), 0.0), roughness);
  const float ggx1 = GeometrySchlickGGX(max(dot(N, L), 0.0), roughness);
  return ggx1 * ggx2;
}

vec3 directional_light(vec3 N, vec3 V, Light light, vec3 F0) {
  // Direction vector
  const vec3 D = normalize(light.position - light.direction);
  const vec3 H = normalize(V + D);

  // Shadow mapping - find the closest and current depth for this fragment
  const float current_depth = shadow_coord.z;
  const float closest_depth = textureProj(shadow_map_tex, shadow_coord);
  // Force shadow off if z is outside the far plane of the frustum
  const float shadow = mix(closest_depth, 1.0, 1.0 - step(1.0, current_depth));
  // ... equivalent of: 
  // float shadow = closest_depth;
  // if (current_depth < 0.0) {
  //   shadow = 1.0;
  // }

  // Radiance for directional lights is the color of the light times its strength
  const vec3 radiance = light.color * light.strength;

  // Calculate normal distribution for specular brdf.
  const float NDF = DistributionGGX(N, H, material.d);

  // Calculate geometric attenuation for specular brdf.
  const float G = GeometrySmith(N, V, D, material.d);

  // Calculate Fresnel term for direct lighting. 
  const vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

  // Diffuse scattering
  const vec3 kD = (vec3(1.0) - F) * (1.0 - material.s); 

  // Cook-torrance brdf
  const float n_dot_l = max(dot(N, D), 0.0);
  const float denominator = 4.0 * max(dot(N, V), 0.0) * n_dot_l + 0.0001;
  const vec3 specular = (NDF * G * F) / denominator;

  // Composition
  return (((kD * material.a / PI + specular) * shadow) * radiance * n_dot_l);
}

vec3 point_light(vec3 N, vec3 V, PointLight light, vec3 F0) {
  // Direction vector
  const vec3 frag_pos = vec3(frag_world_pos);
  const vec3 D = normalize(light.position - frag_pos);
  const vec3 H = normalize(V + D);

  // Attenuation
  const float distance = length(light.position - frag_pos);
  const float strength = light.strength;
  const float attenuation = light.strength / distance; // Basic attenuation for now, usually this would be / pow(distance, 2.0)
  // More complex attenuation formula that uses a linear and quadratic term from the light; and the strength is the constant.
  // const float light_quadratic = 0.09;
  // const float light_linear = 0.032;
  // const float attenuation = 1.0 / (light.strength + light_linear * distance + light_quadratic * pow(distance, 2.0));  

  // Radiance is the product of the color and the attenuation
  const vec3 radiance = light.color * attenuation * strength;

  // Calculate normal distribution for specular brdf.
  const float NDF = DistributionGGX(N, H, material.d);

  // Calculate geometric attenuation for specular brdf.
  const float G = GeometrySmith(N, V, D, material.d);

  // Calculate Fresnel term for direct lighting. 
  const vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

  // Diffuse scattering
  const vec3 kD = (vec3(1.0) - F) * (1.0 - material.s);

  // Cook-torrance brdf
  const float n_dot_l = max(dot(N, D), 0.0);
  const float denominator = 4.0 * max(dot(N, V), 0.0) * n_dot_l + 0.0001;
  const vec3 specular = (NDF * G * F) / denominator;

  // Composition
  return ((kD * material.a / PI + specular)) * radiance * n_dot_l;
}

vec3 spot_light(vec3 N, vec3 V, SpotLight light, vec3 F0) {
  // Direction vector
  const vec3 frag_pos = vec3(frag_world_pos);
  const vec3 D = normalize(light.position - frag_pos);
  const vec3 H = normalize(V + D);

  // Cutoff angle for spot light
  const float theta = dot(D, -light.direction);
  const float epsilon = light.cutoff - light.softness;
  // const float intensity = clamp((theta - light.softness) / epsilon, 0.0, 1.0);
  const float intensity = smoothstep(0.0, 1.0, (theta - light.softness) / epsilon);

  // Attenuation
  const float distance = length(light.position - frag_pos);
  const float strength = light.strength;
  const float attenuation = light.strength / distance; // Basic attenuation for now, usually this would be / pow(distance, 2.0)
  // More complex attenuation formula that uses a linear and quadratic term from the light; and the strength is the constant.
  // const float light_quadratic = 0.09;
  // const float light_linear = 0.032;
  // const float attenuation = 1.0 / (light.strength + light_linear * distance + light_quadratic * pow(distance, 2.0));  

  // Radiance is the product of the color and the attenuation
  const vec3 radiance = light.color * attenuation * strength;

  // Calculate normal distribution for specular brdf.
  const float NDF = DistributionGGX(N, H, material.d);

  // Calculate geometric attenuation for specular brdf.
  const float G = GeometrySmith(N, V, D, material.d);

  // Calculate Fresnel term for direct lighting. 
  const vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

  // Diffuse scattering
  const vec3 kD = (vec3(1.0) - F) * (1.0 - material.s);

  // Cook-torrance brdf
  const float n_dot_l = max(dot(N, D), 0.0);
  const float denominator = 4.0 * max(dot(N, V), 0.0) * n_dot_l + 0.0001;
  const vec3 specular = (NDF * G * F) / denominator;

  // Composition
  return ((kD * material.a / PI + specular)) * intensity * radiance * n_dot_l;
}

vec3 skybox_colors(vec3 tex_color) {
  const vec3 frag_pos = vec3(frag_world_pos);
  const vec3 V = normalize(cam_pos - frag_pos);

  // Precompute the surface response at normal incidence
  const vec3 F0 = mix(vec3(0.04), skybox_material.a, skybox_material.s);

  // Direction vector
  const vec3 D = normalize(global_light.position - global_light.direction);
  const vec3 H = normalize(V + D);

  // Radiance for directional lights is the color of the light times its strength
  const vec3 radiance = global_light.color * global_light.strength;

  // Calculate Fresnel term for direct lighting.
  const vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

  // Diffuse scattering
  const vec3 kD = (vec3(1.0) - F) * (1.0 - skybox_material.s); 

  // Only using the global light
  vec3 Lo = (((kD * skybox_material.a / (PI + skybox_material.d))) * radiance);

  // Blend texture color with the combined illumination (if 0 there is none)
  return Lo * tex_color;
}

vec3 light_colors(vec3 tex_color) {
  const vec3 frag_pos = vec3(frag_world_pos);
  const vec3 V = normalize(cam_pos - frag_pos);

  // Precompute the surface response at normal incidence
  const vec3 F0 = mix(vec3(0.04), material.a, material.s);

  // Directional lights
  vec3 Lo = directional_light(normal, V, global_light, F0);

  if (local_light_blend > 0.0) {
    for (int i = 0; i < max_lights; i++) {
      Lo += point_light(normal, V, lights[i], F0);
      if (i == num_lights) {
        break;
      }
    }
  }

  // Spot light such as camera positioned flash light
  Lo += spot_light(normal, V, flash_light, F0);

  // Skybox reflection
  const vec3 I = normalize(frag_pos - cam_pos);
  const vec3 R = reflect(I, normalize(normal)); 
  // const vec3 R = refract(I, normalize(normal), 1.00 / 1.52); // Displacement via refraction with the given refractive index:
  // Air: 1.00 / 1.00
  // Water: 1.00 / 1.33
  // Ice: 1.00 / 1.309
  // Glass: 1.00 / 1.52
  // Diamond: 1.00 / 2.42
  const vec3 skybox_reflection = texture(u_cube_map, R).rgb; // Reflection/Refraction texture rgb
  const vec3 skybox_color = skybox_colors(skybox_reflection); // Apply light to match the skybox illumination
  tex_color = mix(tex_color, skybox_color, material.r); // Mix into texture

  // Blend texture color with the combined illumination (if 0 there is none)
  return Lo * mix(vec3(1.0), tex_color, texture_blend);
}

void main() {
  vec3 color = texture(u_tex_albedo, uv_0).rgb;
  color = pow(color, gamma);
  color = light_colors(color);

  // Fog
  // const float fog = gl_FragCoord.z / gl_FragCoord.w; // Strength higher when far away from frag
  // color = mix(color, fog_albedo, (1.0 - exp2(-fog_scale * fog)));

  color = pow(color, i_gamma);
  frag_color = vec4(color, 1.0);
}