# Prompts for the character parts sheet

Keep prompts short. Image generators draw separate simple pieces well, but they cannot invent hidden geometry
("extend the sleeve by 20%") and they distort parts when one prompt asks for too many things.
The hidden-joint overlaps (filled shoulders on the torso, longer neck, extended joint ends) are added afterwards
by code or by hand, not by the image tool.

## Step 1: the character (attach the childhood photo, face only)

```
Cartoon boy character, 2D flat vector style, thick dark outline, flat colors.
Use the attached photo only for the face (face shape, eyes, nose, smile, hair).
Full body, front view, standing, arms hanging down, mouth closed.
Outfit: [your outfit]. Plain white background, no text.
```

## Step 2: the parts sheet (attach the character image from step 1)

```
Character sheet for 2D cut-out animation, same character as the attached image.
Show separate parts on a plain white background, spaced apart:
bald head with a blank face (no eyes, nose, mouth), hair pieces, torso without sleeves,
upper arms with sleeves, forearms, hands, shorts, legs with shoes,
eyes, eyebrows, nose, and mouths (closed, half open, open).
Flat vector style, thick outline, no text, no labels.
```

If the parts come out distorted, split step 2 into two images: one for the body (head, torso, arms, hands, shorts,
legs) and one for the face (eyes, eyebrows, nose, mouths).

## Uniqueness check

Reverse-image search the final design (Google Lens, TinEye) and search the character name on YouTube and Google.

## Done later by code or by hand (do not ask the image tool)

- Fill the shoulders of the torso so no gap shows when the sleeve rotates.
- Longer neck hidden under the collar, separate nose layer.
- Extend the ends of arm/leg pieces where they join.
