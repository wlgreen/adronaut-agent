# Ad Generation Workflow & Data Requirements

**Complete guide to generating AI-powered ad creatives**

Last Updated: October 21, 2025

---

## Quick Start

### Standalone Test Workflow

```bash
python cli.py test-creative \
  --product-description "Premium wireless headphones with active noise cancellation" \
  --platform Meta \
  --audience "Tech enthusiasts 25-40" \
  --creative-style "Aspirational lifestyle" \
  --keywords "noise cancellation,wireless,premium" \
  --brand-name "AudioTech" \
  --product-image /path/to/product.jpg
```

**Output:** JSON file with complete creative ready for image generation + quality rating

---

## Complete 4-Step Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AD GENERATION WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

   INPUT                STEP 1              STEP 2              STEP 3           STEP 4
     │                    │                    │                   │                │
     │              ┌──────────┐         ┌──────────┐        ┌─────────┐      ┌────────┐
     │              │ Generate │         │  Review  │        │  Final  │      │  Rate  │
     ├─────────────▶│ Initial  │────────▶│    &     │───────▶│Creative │─────▶│Quality │
     │              │  Prompt  │         │ Upgrade  │        │ Output  │      │        │
     │              └──────────┘         └──────────┘        └─────────┘      └────────┘
     │                    │                    │                   │                │
     │              LLM Creates          LLM Reviews         Validates &      Scores 0-100
     │              Visual Prompt        Against 10pt        Prepares for     8 Categories
     │              + Ad Copy            Checklist           Image Gen
     │              + 5 Hooks
     │
     ▼

REQUIRED DATA:
• Product Description
• Platform (Meta/TikTok/Google)

OPTIONAL DATA:
• Product Image
• Target Audience
• Creative Style
• Required Keywords
• Brand Name
```

---

## Data Requirements

### Required Inputs

#### 1. **Product Description** (REQUIRED)
```
What it is: Detailed description of your product/service
Format: Plain text, 50-500 words
Example: "Premium wireless headphones with active noise cancellation,
         40-hour battery life, premium leather ear cups, and studio-quality
         sound. Perfect for commuters, travelers, and audiophiles."

Used for: LLM understands what to show in visual prompt and copy
```

#### 2. **Platform** (REQUIRED)
```
What it is: Where the ad will run
Options:
  • Meta (Facebook/Instagram) - Default
  • TikTok
  • Google Ads

Impact:
  • Meta: 1:1, 4:5, 9:16 aspect ratios
  • TikTok: 9:16 (primary), 1:1 (secondary)
  • Google: 1.91:1, 1:1

Copy limits:
  • Meta: 125 chars (primary), 40 chars (headline)
  • TikTok: 100 chars
  • Google: 30 chars (headline), 90 chars (description)
```

### Optional Inputs (Enhance Quality)

#### 3. **Product Image** (OPTIONAL, Recommended)
```
What it is: Photo of your actual product
Format: JPG, PNG (any size)
Example: /path/to/headphones.jpg

Used for:
  • LLM analyzes actual product appearance
  • Maintains exact proportions and colors
  • Accurate material description (leather, metal, fabric)
  • Logo placement and size

Impact: +20-30% prompt accuracy and product fidelity
```

#### 4. **Target Audience** (OPTIONAL)
```
What it is: Who you're targeting
Format: Descriptive text
Examples:
  • "Tech enthusiasts 25-40"
  • "Fitness-focused millennials"
  • "Small business owners"

Default: "General audience"

Used for:
  • Visual style (professional vs casual)
  • Copy tone (technical vs emotional)
  • Scene setting (office vs gym vs outdoors)
```

#### 5. **Creative Style** (OPTIONAL)
```
What it is: Visual and tonal direction
Format: Style descriptor
Examples:
  • "Aspirational lifestyle"
  • "User-generated content (UGC)"
  • "Professional product demo"
  • "Editorial magazine style"
  • "Raw and authentic"

Default: "Professional"

Used for:
  • Photography style (studio vs candid)
  • Lighting (cinematic vs natural)
  • Composition (clean vs dynamic)
```

#### 6. **Required Keywords** (OPTIONAL, for Quality Check)
```
What it is: Keywords that MUST appear in the prompt
Format: Comma-separated list
Example: "noise cancellation,wireless,premium"

Used for:
  • Rating step checks keyword presence
  • Ensures key features mentioned
  • Quality score affected if missing

Impact: Ensures important features aren't missed by LLM
```

#### 7. **Brand Name** (OPTIONAL, for Quality Check)
```
What it is: Your brand name
Format: Plain text
Example: "AudioTech"

Used for:
  • Rating checks brand visibility in prompt
  • Ensures logo/name mentioned
  • Quality score for brand presence

Impact: Ensures brand is prominently featured
```

---

## Step-by-Step Workflow Details

### STEP 1: Generate Initial Creative Prompt

**What Happens:**
- LLM analyzes product description (and image if provided)
- Generates professional creative brief for image generation
- Creates platform-native ad copy
- Writes 5 different hook variations

**LLM Settings:**
- Model: Gemini 2.0 Flash
- Temperature: 0.7 (balanced creativity)
- Task: "Creative Prompt Generation"

**Output Structure:**
```json
{
  "visual_prompt": "A 35-year-old professional commuter wearing the AudioTech
                    wireless headphones sits by a sunlit window on a morning
                    train. Soft golden-hour light filters through, illuminating
                    the premium black leather ear cups with their distinctive
                    copper logo. The headphones rest comfortably around his neck,
                    showing the brushed aluminum headband and fine stitching
                    detail. Shot with shallow depth of field using 85mm lens,
                    f/1.8, creating cinematic bokeh in the background. The mood
                    is calm, focused, premium. Clean negative space on the left
                    for text overlay. Editorial quality, print-ready advertising
                    photography.",

  "copy_primary_text": "Your commute just got an upgrade. These aren't just
                        headphones—they're your escape pod. 40 hours of battery,
                        studio-quality sound, and silence when you need it most.",

  "copy_headline": "Premium Sound, Zero Distractions",

  "copy_cta": "SHOP_NOW",

  "hooks": [
    "Ever notice how the best ideas come when everything's quiet?",
    "I've tested 12 headphones this year. These are the ones I kept.",
    "40-hour battery. I charged them once this month.",
    "Your morning commute could be the best part of your day.",
    "The difference between good and great? It's in the details."
  ],

  "technical_specs": {
    "aspect_ratio": "1:1",
    "dimensions": "1080x1080",
    "file_format": "PNG",
    "file_size_max": "30MB",
    "brand_assets": ["logo_placement: bottom-right, 80x80px"],
    "color_scheme": "#000000 (primary), #FFFFFF (text), #CD7F32 (copper accent)"
  }
}
```

**Key Features of Visual Prompts:**
- 250-600 words of rich visual description
- Photographic realism (not illustration)
- Cinematic lighting and camera details
- Product occupies ~1/3 of frame
- Exact proportions from product image
- Professional photographer language
- Platform-appropriate composition

### STEP 2: Review and Upgrade Prompt

**What Happens:**
- LLM reviews visual prompt against 10-point quality checklist
- Upgrades prompt if issues found
- Returns reviewed prompt with notes

**10-Point Review Checklist:**
1. ✅ Product clearly visible (1/3 of frame)
2. ✅ Exact proportions maintained
3. ✅ Lighting details specified
4. ✅ Camera/lens details included
5. ✅ Texture and materials described
6. ✅ Composition and mood defined
7. ✅ Brand tone appropriate
8. ✅ No generic clichés
9. ✅ Cinematic/editorial quality
10. ✅ Text overlay space noted

**LLM Settings:**
- Model: Gemini 2.0 Flash
- Temperature: 0.3 (focused, analytical)
- Task: "Creative Review & Upgrade"

**Output Structure:**
```json
{
  "reviewed_prompt": "Enhanced version of visual prompt (if changes made)",
  "changed": true/false,
  "notes": "Explanation of changes made or why prompt passed",
  "review_scores": {
    "product_visibility": 10,
    "proportion_accuracy": 9,
    "lighting_detail": 10,
    // ... scores for all 10 criteria
  }
}
```

**Example Upgrade:**
```
BEFORE: "Person wearing headphones in office"

AFTER:  "A 35-year-old professional wearing the AudioTech wireless
         headphones sits at a minimalist desk by a floor-to-ceiling
         window. Morning sunlight creates soft rim lighting on the
         premium black leather ear cups, highlighting the brushed
         aluminum headband and copper logo. Shot at eye level with
         85mm lens, f/2.8, shallow depth of field. Product positioned
         at natural ear level, fully visible, unobstructed..."
```

### STEP 3: Final Creative Output

**What Happens:**
- Takes reviewed prompt as final creative
- Validates against platform requirements
- Packages everything for image generation

**Validation Checks:**
```
✓ Visual prompt exists and is non-empty
✓ Copy within platform character limits
✓ All required fields present
✓ Technical specs match platform
✓ Hooks array has exactly 5 entries
```

**Output Structure:**
```json
{
  "final_visual_prompt": "The reviewed, production-ready prompt",
  "copy_primary_text": "Platform-compliant ad copy",
  "copy_headline": "40 chars or less for Meta",
  "copy_cta": "SHOP_NOW",
  "hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
  "technical_specs": { ... },
  "ready_for_image_generation": true,
  "validation": {
    "is_valid": true,
    "errors": []
  }
}
```

### STEP 4: Rate Creative Quality

**What Happens:**
- LLM scores prompt on 8 criteria (0-10 each)
- Analyzes keyword presence
- Checks brand visibility
- Evaluates platform adherence
- Provides actionable feedback

**8 Rating Categories:**

1. **Keyword Presence** (0-10)
   - Checks if required keywords appear
   - Example: "noise cancellation", "wireless", "premium"

2. **Brand/Logo Visibility** (0-10)
   - Brand name mentioned in prompt
   - Logo placement described

3. **Prompt Adherence** (0-10)
   - Matches platform requirements
   - Appropriate for target audience
   - Follows creative style direction

4. **Visual Clarity** (0-10)
   - Clear, specific descriptions
   - Not generic or vague

5. **Product Fidelity** (0-10)
   - Accurate representation
   - Maintains proportions
   - Materials described correctly

6. **Professional Quality** (0-10)
   - Cinema-quality language
   - Editorial photography standards

7. **Completeness** (0-10)
   - All required elements present
   - Technical specs included

8. **Authenticity** (0-10)
   - Platform-appropriate voice
   - Not overly promotional

**LLM Settings:**
- Model: Gemini 2.0 Flash
- Temperature: 0.3 (analytical, consistent)
- Task: "Creative Quality Rating"

**Output Structure:**
```json
{
  "overall_score": 85,
  "category_scores": {
    "keyword_presence": 9,
    "brand_visibility": 10,
    "prompt_adherence": 9,
    "visual_clarity": 10,
    "product_fidelity": 8,
    "professional_quality": 9,
    "completeness": 8,
    "authenticity": 9
  },
  "keyword_analysis": {
    "required_keywords": ["noise cancellation", "wireless", "premium"],
    "found_keywords": ["noise cancellation", "wireless", "premium"],
    "missing_keywords": [],
    "keyword_score": 10
  },
  "brand_presence": {
    "brand_mentioned": true,
    "logo_described": true,
    "prominence_score": 10
  },
  "strengths": [
    "Excellent product visibility with clear 1/3 frame composition",
    "Professional photography language with specific camera details",
    "Strong brand presence with logo placement described"
  ],
  "weaknesses": [
    "Could add more texture description for leather ear cups",
    "Background detail slightly generic"
  ],
  "suggestions": [
    "Consider adding specific stitching pattern detail",
    "Describe copper logo finish (matte vs glossy)"
  ]
}
```

**Score Interpretation:**
- **90-100**: Exceptional - Ready for premium campaigns
- **80-89**: Excellent - Minor tweaks optional
- **70-79**: Good - Usable with some improvements
- **60-69**: Needs Work - Review suggestions carefully
- **<60**: Regenerate - Major issues found

---

## Final Output Format

### Saved to: `output/test_creatives/test_creative_[timestamp].json`

```json
{
  "success": true,
  "workflow_steps": {
    "step1_generation": { ... },
    "step2_review": { ... },
    "step3_creative": { ... },
    "step4_rating": { ... }
  },
  "summary": {
    "platform": "Meta",
    "audience": "Tech enthusiasts 25-40",
    "creative_style": "Aspirational lifestyle",
    "prompt_changed_in_review": true,
    "final_score": 85,
    "validation_passed": true
  },
  "metadata": {
    "product_description": "...",
    "product_image": "/path/to/image.jpg",
    "platform": "Meta",
    "audience": "Tech enthusiasts 25-40",
    "creative_style": "Aspirational lifestyle"
  }
}
```

---

## Platform-Specific Requirements

### Meta (Facebook/Instagram)

**Aspect Ratios:**
- Feed: 1:1 (1080x1080) - Square, most common
- Stories: 9:16 (1080x1920) - Vertical, full screen
- Mobile Feed: 4:5 (1080x1350) - Portrait

**Copy Limits:**
- Primary Text: 125 characters
- Headline: 40 characters
- Description: 30 characters

**Visual Style:**
- Editorial lifestyle imagery
- Aspirational but attainable
- Cinematic lighting
- Magazine-quality composition

**File Requirements:**
- Format: PNG, JPG
- Max Size: 30MB
- Resolution: Min 1080x1080

### TikTok

**Aspect Ratios:**
- Primary: 9:16 (1080x1920) - Full screen vertical
- Secondary: 1:1 (1080x1080) - Square

**Copy Limits:**
- Text: 100 characters

**Visual Style:**
- Authentic, raw moments
- Unfiltered yet polished
- Natural lighting
- Candid compositions

**File Requirements:**
- Format: PNG, JPG
- Max Size: 500MB
- Resolution: Min 1080x1920

### Google Ads

**Aspect Ratios:**
- Responsive: 1.91:1 (1200x628) - Landscape
- Square: 1:1 (1080x1080)

**Copy Limits:**
- Headline: 30 characters
- Description: 90 characters

**Visual Style:**
- Clean, informative
- Product-focused
- Studio or natural light
- Clear focal point

**File Requirements:**
- Format: PNG, JPG
- Max Size: 5MB
- Resolution: Min 1200x628

---

## Example Usage Patterns

### 1. Quick Test (Minimal Data)

```bash
python cli.py test-creative \
  --product-description "Eco-friendly water bottle" \
  --platform Meta
```

**What you get:**
- Generic but professional creative
- Default "General audience" targeting
- "Professional" creative style
- Score: ~70-75 (good baseline)

### 2. Standard Test (Recommended)

```bash
python cli.py test-creative \
  --product-description "Eco-friendly insulated water bottle, keeps drinks cold 24hrs" \
  --platform Meta \
  --audience "Fitness-focused millennials 25-40" \
  --creative-style "Aspirational lifestyle"
```

**What you get:**
- Audience-specific visuals and copy
- Platform-native tone
- Clear creative direction
- Score: ~80-85 (excellent)

### 3. Premium Test (Maximum Quality)

```bash
python cli.py test-creative \
  --product-description "Premium insulated water bottle with triple-wall vacuum
                         technology. Keeps drinks cold for 24 hours, hot for 12.
                         BPA-free stainless steel with powder-coated finish.
                         Leak-proof cap with carrying loop." \
  --product-image /path/to/bottle_photo.jpg \
  --platform Meta \
  --audience "Eco-conscious fitness enthusiasts, 25-40, active lifestyle" \
  --creative-style "Editorial lifestyle - aspirational outdoor adventure" \
  --keywords "24-hour cold,eco-friendly,BPA-free,leak-proof" \
  --brand-name "HydroLife"
```

**What you get:**
- Precise product representation
- Brand-aligned visuals
- All keywords included
- Logo placement described
- Score: ~90-95 (exceptional)

---

## Integration with Full Campaign Workflow

### Standalone (Test Creative)
```
You → test-creative command → 4-step workflow → JSON output
```
**Use case:** Testing creative ideas, quality checking prompts

### Full Agent Workflow
```
Historical Data → Strategy → Execution Timeline → [Creative Gen for each combo]
                                                              ↓
                                               Campaign Config with Creative Assets
```
**Use case:** Production campaigns with multiple test combinations

**Example:** Strategy creates 12 test combinations (4 audiences × 3 platforms):
- Each gets custom creative via same 4-step workflow
- All packaged in `campaign_[project]_v0.json`
- Ready for Meta Ads API deployment

---

## Quality Tips

### To Maximize Prompt Quality:

1. **Detailed Product Description**
   - Include materials, colors, dimensions
   - Mention key features and benefits
   - Add any unique design elements

2. **Provide Product Image**
   - Use high-quality reference photo
   - Shows actual product, not mockup
   - +20-30% accuracy improvement

3. **Specific Audience**
   - Age range, interests, lifestyle
   - More specific = better targeting
   - Example: "Urban professionals 28-35 who commute by bike"

4. **Clear Creative Style**
   - Match your brand identity
   - Consider platform culture
   - Example: "Clean minimalist studio photography" vs "Raw UGC iPhone video"

5. **Required Keywords**
   - List 3-5 must-have features
   - Ensures they appear in prompt
   - Drives quality score

6. **Brand Name**
   - Enables brand visibility checks
   - Logo placement validation
   - Consistent brand presence

---

## Troubleshooting

### Low Quality Score (<70)

**Check:**
- Is product description too vague?
- Missing required keywords?
- Creative style unclear?

**Fix:**
- Add more detail to description
- Specify keywords explicitly
- Define creative style clearly
- Provide product image

### Prompt Doesn't Match Product

**Likely Cause:**
- No product image provided
- LLM filled in missing details

**Fix:**
- Always provide product image for accuracy
- Describe unique features in detail

### Copy Too Long

**Cause:**
- Platform limits exceeded
- LLM didn't respect constraints

**Fix:**
- Check `copy_limits` in output
- Workflow should auto-truncate
- Review Step 3 validation errors

### Generic Visuals

**Cause:**
- Audience or style not specified
- Default "General audience" used

**Fix:**
- Provide specific audience description
- Define creative style explicitly
- Add brand guidelines if available

---

## API Reference

### run_test_creative_workflow()

```python
from src.workflows.test_creative_workflow import run_test_creative_workflow

results = run_test_creative_workflow(
    product_description: str,              # REQUIRED
    product_image_path: Optional[str],     # Recommended
    platform: str = "Meta",                # Default: Meta
    audience: Optional[str] = None,        # Default: "General audience"
    creative_style: Optional[str] = None,  # Default: "Professional"
    required_keywords: Optional[List[str]] = None,
    brand_name: Optional[str] = None
)
```

**Returns:** Dict with complete workflow results

---

## Next Steps

1. **Test the Workflow:**
   ```bash
   python cli.py test-creative --product-description "Your product" --platform Meta
   ```

2. **Review Output:**
   - Check `output/test_creatives/test_creative_*.json`
   - Examine visual prompt quality
   - Review rating scores

3. **Iterate:**
   - Add product image if score < 80
   - Refine audience description
   - Adjust creative style
   - Add required keywords

4. **Production Use:**
   - Integrate with full agent workflow
   - Generate creatives for entire campaign
   - Deploy to Meta Ads API (coming soon)

---

## Resources

- **Creative Generator Module:** `src/modules/creative_generator.py`
- **Test Workflow:** `src/workflows/test_creative_workflow.py`
- **Creative Rater:** `src/modules/creative_rater.py`
- **Platform Specs:** `PLATFORM_SPECS` dict in creative_generator.py
- **CLI Usage:** `python cli.py test-creative --help`

---

**Questions?** Check `docs/CREATIVE_GENERATION.md` for technical implementation details.
