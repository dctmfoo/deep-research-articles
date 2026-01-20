---
name: imagen-prompting
description: "Guidelines for generating effective image prompts for Gemini 3 Pro Image. Use when creating image prompts for article visuals."
---

# Imagen Prompting Guide (Nano Banana Pro)

State-of-the-art image generation. **This model is extremely capable** - describe something clearly and in detail, it will generate exactly what you describe.

## Core Principle

**Describe the scene, don't just list keywords.** Narrative, descriptive paragraphs outperform keyword lists. The model understands natural language.

You don't need "4k, trending on artstation, masterpiece" spam. Just describe what you want clearly.

## Prompt Structure

```
[Subject + Adjectives] doing [Action] in [Location/Context].
[Composition/Camera Angle]. [Lighting/Atmosphere]. [Style/Media].
```

## Key Elements

| Element | Examples |
|---------|----------|
| **Subject** | "elderly Japanese ceramicist", "minimalist coffee mug", "red panda" |
| **Details** | "deep sun-etched wrinkles", "matte black finish", "wearing a tiny bamboo hat" |
| **Setting** | "in a traditional pottery studio", "on wet city street at night" |
| **Camera** | "close-up portrait", "wide-angle shot", "bird's eye view" |
| **Lighting** | "soft natural light", "dramatic studio lighting", "golden hour" |
| **Style** | "photorealistic", "kawaii-style sticker", "minimalist vector art" |

---

## Example Prompts

### Photorealistic Portrait
```
A photorealistic close-up portrait of an elderly Japanese ceramicist with deep,
sun-etched wrinkles and a warm, knowing smile. Soft natural light from a nearby
window illuminates their weathered hands holding a delicate tea bowl. Background
shows blurred pottery studio with wooden shelves.
```

### Product Photography
```
A high-resolution, studio-lit product photograph of a minimalist ceramic coffee
mug in matte black. Clean white background with subtle shadow. The mug is
positioned at a 3/4 angle showing both the handle and interior. Sharp focus,
commercial photography style.
```

### Stylized/Kawaii
```
A kawaii-style sticker of a happy red panda wearing a tiny bamboo hat, holding
a bubble tea cup. The design features bold, clean outlines, simple cel-shading,
pastel pink and mint green color palette. White background, die-cut sticker format.
```

### Logo/Text Design
```
Create a modern, minimalist logo for a coffee shop called 'The Daily Grind'.
The text should be in a clean, bold, sans-serif font. Include a simple geometric
coffee cup icon. Colors: deep brown and cream. Suitable for signage and packaging.
```

### Text in Images
Don't just say "add text." Be specific:
```
A vintage-style travel poster for Berlin. The word 'BERLIN' appears in large,
bold red serif letters at the top. Below shows the Brandenburg Gate at sunset
with dramatic orange and purple sky. 1950s tourism poster aesthetic.
```

### Infographics
```
Generate a step-by-step infographic showing how to make Elaichi Chai. Include
accurate ingredients: cardamom pods, loose tea leaves, milk, sugar, ginger.
Style: Clean vector art with pastel colors. Number each step 1-5. Label all
ingredients clearly in a modern sans-serif font.
```

### Lifestyle/Scene
```
A cozy reading nook in a Scandinavian-style apartment. Large window with rain
drops, grey afternoon light. A person in an oversized sweater curled up on a
cream linen armchair with a book. Warm throw blanket, steaming cup of tea on
side table. Hygge atmosphere, soft focus background.
```

---

## Text Rendering Tips

The model excels at legible text in images. For best results:

1. **Quote the exact text**: `Write the text 'HELLO WORLD'`
2. **Specify font style**: `bold, red, serif font` or `handwritten script`
3. **Indicate placement**: `centered at the top`, `on the wooden sign`
4. **Give context**: `as a neon sign`, `carved into stone`, `on a chalkboard`

---

## Aspect Ratios

| Use Case | Aspect Ratio |
|----------|--------------|
| Article headers | 16:9 |
| Social media | 1:1 |
| Portraits | 3:4 or 4:3 |
| Mobile/Stories | 9:16 |

---

## Output Format for Prompts

When generating prompts for the synthesizer, output JSON:

```json
{
  "prompts": [
    {
      "description": "Full descriptive prompt",
      "style": "photorealistic|illustration|diagram|vector|etc",
      "quality_modifiers": ["high-quality", "detailed", "professional"],
      "aspect_ratio": "16:9",
      "purpose": "header|diagram|visual|infographic"
    }
  ]
}
```

## Limitations

- Small faces and fine details may not always be perfect
- Text spelling can occasionally have errors - verify important text
- Data-driven outputs (charts, diagrams) should be fact-checked
