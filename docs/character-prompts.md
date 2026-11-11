# Prompts for a character that can be rigged (with hidden-joint overlaps)

Use four separate prompts (one image each) so every piece comes out large and sharp. Replace the text in [brackets].

How to use the references:
- Prompt A: attach the **childhood photo** (face only).
- Prompt B and C: attach the **character design produced by Prompt A**, not the photo.
- Prompt D: attach the character design **and** the photo (for the face features).

Why the magenta background: it never appears in the character, so it can be removed cleanly afterwards.

---

## Prompt A: character design

```
Create an original 2D cartoon character design of a boy, about 8 years old, for a children's animated series.

Use the attached photo ONLY as a reference for the facial features: face shape, eye shape and spacing, eyebrows, nose, smile, ears, hair colour and hair texture. Do NOT copy the clothes, pose, background or lighting from the photo. Stylize it completely as a flat 2D cartoon: clean vector look, thick uniform dark outline, flat colours with at most one soft shade tone. It must NOT look photorealistic or like a 3D render.

Outfit: [for example: a short-sleeve hoodie in colour X with a small distinctive emblem, shorts in colour Y, sneakers in colour Z with white socks]. One signature item that makes him recognisable: [for example: a small yellow backpack / a cap / a scarf]. 

Full body, front view, orthographic (no perspective), standing straight, arms hanging down slightly away from the body, neutral friendly expression, mouth closed. Solid flat magenta (#FF00FF) background, no shadows, no text, no watermark.
```

## Prompt B: body parts sheet

```
Using the attached character design as the exact reference (same style, colours, outline thickness and proportions), draw a cut-out animation PARTS SHEET of the same character for a 2D puppet rig.

Rules for the whole sheet:
- Flat solid magenta (#FF00FF) background.
- Every part is a separate isolated piece, front view, NOT touching or overlapping any other piece, with at least 60 px of empty space around it.
- No labels, no text, no numbers, no arrows, no joint dots, no shadows.
- All parts are drawn at the same scale they have on the assembled character, with the same thick outline.

Pieces (each exactly once):
1. HEAD BASE: the head with both ears and the neck, with a COMPLETELY BLANK face: no eyes, no eyebrows, no nose, no mouth, no blush marks, no hair (bald). The neck is drawn longer than normal: it continues down for about 25% of the head height so it can hide under the shirt collar.
2. HAIR: the front hair / fringe piece, and a separate back hair piece.
3. TORSO: the shirt body WITHOUT sleeves, drawn complete: the shoulders are filled with shirt colour and there are no armhole openings, so nothing is missing underneath the sleeves. Include the collar/hood and the shirt design.
4. SHORTS: one piece. The waist is extended upward by about 20% beyond the normal waistline (this extra part is hidden under the shirt). Two leg openings.
5. LEGS: left and right separate pieces, each is leg + sock + shoe, straight and vertical, shoes facing forward. The top end of each leg is extended by about 20% (hidden under the shorts).
6. The signature item ([backpack / cap / scarf]) as a separate piece, if it exists.
```

## Prompt C: arms and hands (hidden-joint overlaps)

```
Using the attached character design as the exact reference (same style, colours, outline thickness and proportions), draw the ARM PARTS for a 2D puppet rig. Flat solid magenta (#FF00FF) background. Every piece is isolated, front view, with at least 60 px empty space around it. No labels, no text, no joint dots, no shadows. Same scale as on the assembled character.

Draw ONE arm (I will mirror it for the other side), as three kinds of pieces, all hanging straight down along a vertical axis:

1. UPPER ARM WITH SLEEVE: the sleeve at the top and the bare upper arm below it. The top (shoulder end) is a fully closed rounded cap, extended about 20% beyond the real shoulder point, so it can sit inside the shoulder without showing a gap when it rotates. The lower (elbow) end is plain skin, rounded, extended about 15% beyond the elbow.
2. FOREARM: skin only, straight and vertical. BOTH ends are rounded and extended about 15% longer than normal (the top end hides under the elbow, the bottom end hides inside the hand).
3. HANDS: six separate hands, all on the same vertical axis as the forearm, palm facing the viewer, each with a short wrist stub (about 20% extra) at the top so it can hide inside the forearm: relaxed hand, fully open hand with spread fingers (for waving), pointing hand with only the index finger extended along the arm axis (pointing down), closed fist, thumbs up, and a hand holding a small round object.
```

## Prompt D: face parts

```
Using the attached character design as the style reference, and the attached photo ONLY for the facial features (eye shape, eyebrows, nose, smile), draw the FACE PARTS of the same character as separate isolated pieces for a 2D puppet rig. Flat solid magenta (#FF00FF) background. At least 60 px empty space around every piece. No head, no labels, no text, no numbers, no shadows. Same scale and outline thickness as the assembled character's face.

Pieces:
- EYES (pairs, left and right together in the correct spacing): open eyes, closed eyes (blink), happy smiling closed eyes (arches), surprised wide-open eyes, angry eyes, sad eyes.
- EYEBROWS as separate pairs (not attached to the eyes): neutral, raised, angry, sad.
- NOSE: two small cartoon noses (front view).
- MOUTHS, each separate: closed smile, closed neutral, small round "oh", half open, wide open "ah" with teeth and tongue, wide smile showing teeth, sad frown, big laugh.
```

---

## Checklist before sending me the images

- [ ] Magenta background everywhere, no gradients, no shadow under the pieces.
- [ ] Pieces are separate with clear space between them (no touching).
- [ ] The head has NO eyes, nose, mouth, eyebrows or hair.
- [ ] Torso has no armhole openings; shorts waist and leg tops are visibly longer than needed.
- [ ] Upper arm, forearm and hands have the extra hidden length at the joint ends.
- [ ] All hands hang on the same vertical axis as the forearm.
- [ ] Same outline thickness and colours across all four images.

If a tool cannot make the hidden extensions correctly, tell me: I can extend the ends of the pieces, or you can paint them in Krita / Photopea.

Check the result for uniqueness before using it: reverse-image search the final design (Google Lens, TinEye) and search the character name on YouTube and Google.
