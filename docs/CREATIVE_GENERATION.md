# Creative Generation Integration

## Overview

The Creative Generation system transforms execution timelines into actionable creative briefs by automatically generating AI-ready image prompts and ad copy for each test combination. This enables:

- **Immediate value**: Clear creative direction for campaign execution
- **Future automation**: Direct integration with AI image generators (DALL-E, Midjourney, Stable Diffusion)
- **Meta Ads ready**: Structured output compatible with Meta Marketing API

## Architecture

### Flow Diagram

```
Historical Data → Strategy Generation → Execution Timeline → Creative Prompts → Campaign Config
                                              ↓
                                      [Per Test Combination]
                                       - Visual Prompt
                                       - Ad Copy
                                       - Hooks (5 variations)
                                       - Technical Specs
```

### Components

1. **`src/modules/creative_generator.py`**: Core creative prompt generation
2. **`src/modules/execution_planner.py`**: Integration point (enhances test combinations)
3. **`src/modules/campaign.py`**: Includes creative assets in final output
4. **`src/integrations/image_generator.py`**: Future text-to-image integration (stub)
5. **`src/integrations/meta_ads.py`**: Future Meta API deployment (stub)

## How It Works

### 1. Strategy-Driven Creative Generation

For each test combination in the execution timeline, the system generates creative prompts based on:

- **Platform requirements** (TikTok 9:16 vs Meta 1:1)
- **Audience segment** (Gen-Z vs Millennials → different visual styles)
- **Messaging angle** from strategy (value-focused, urgency-driven, etc.)
- **Creative style** (UGC, lifestyle, product demo)
- **Brand guidelines** from user inputs

### 2. LLM-Powered Prompt Generation

**Temperature: 0.7** (balance creativity with brand consistency)

The LLM generates:
- **Visual prompt**: 50-150 word detailed description for AI image generation
- **Ad copy**: Platform-compliant copy (respects character limits)
- **Hooks**: 5 variations testing different psychological angles
- **Technical specs**: Platform-specific dimensions, aspect ratios, file formats

### 3. Platform-Specific Requirements

#### Meta (Facebook/Instagram)
```json
{
  "placements": {
    "feed": "1:1 (1080x1080)",
    "stories": "9:16 (1080x1920)",
    "mobile_feed": "4:5 (1080x1350)"
  },
  "copy_limits": {
    "primary_text": 125,
    "headline": 40,
    "description": 30
  },
  "file_format": "PNG",
  "file_size_max": "30MB"
}
```

#### TikTok
```json
{
  "placements": {
    "primary": "9:16 (1080x1920)",
    "secondary": "1:1 (1080x1080)"
  },
  "copy_limits": {
    "text": 100
  },
  "file_format": "PNG",
  "file_size_max": "500MB"
}
```

#### Google Ads
```json
{
  "placements": {
    "responsive": "1.91:1 (1200x628)",
    "square": "1:1 (1080x1080)"
  },
  "copy_limits": {
    "headline": 30,
    "description": 90
  },
  "file_format": "PNG",
  "file_size_max": "5MB"
}
```

## Output Structure

### Execution Timeline with Creative Prompts

```json
{
  "timeline": {
    "phases": [
      {
        "name": "Short-term Discovery",
        "test_combinations": [
          {
            "id": "combo_1",
            "platform": "Meta",
            "audience": "Millennials 25-34, fitness enthusiasts",
            "creative": "UGC-style lifestyle imagery",
            "budget_percent": 15,
            "creative_generation": {
              "visual_prompt": "High-quality lifestyle photograph, 28-year-old woman in modern minimalist apartment, morning golden hour light through large windows, holding a green smoothie, wearing stylish activewear, yoga mat in background, indoor plants, iPhone photography style, natural warm colors, aspirational yet authentic aesthetic, sharp focus, 1:1 square composition, professional but relatable feel",
              "copy_primary_text": "Join 10,000+ women who transformed their mornings. Our 30-day wellness program fits your busy schedule. Real results, real people.",
              "copy_headline": "Transform Your Mornings in 30 Days",
              "copy_cta": "SHOP_NOW",
              "hooks": [
                "What if your morning routine could change everything?",
                "The wellness secret busy professionals swear by",
                "30 days to a better you - here's exactly how",
                "Why 10K+ women are waking up differently",
                "The morning transformation that fits your life"
              ],
              "technical_specs": {
                "aspect_ratio": "1:1",
                "dimensions": "1080x1080",
                "file_format": "PNG",
                "file_size_max": "30MB",
                "brand_assets": ["logo_placement: bottom-right, 80x80px, 10% opacity"],
                "color_scheme": "#FF5733 (primary), #FFFFFF (text), #2C3E50 (accents)"
              }
            }
          }
        ]
      }
    ]
  }
}
```

### Campaign Config with Creative Assets

```json
{
  "meta": {
    "campaign_name": "...",
    "daily_budget": 500,
    "targeting": {...}
  },
  "creative_assets": [
    {
      "combo_id": "combo_1",
      "phase": "Short-term Discovery",
      "platform": "Meta",
      "audience": "Millennials 25-34, fitness enthusiasts",
      "creative_style": "UGC-style lifestyle imagery",
      "budget_percent": 15,
      "creative_generation": {...}
    }
  ]
}
```

## Usage

### Running the Agent

```bash
# Start agent with historical data
python cli.py run --project-id my-campaign-001

# Upload your historical campaign data
Files: data/historical_campaigns.csv
```

The agent will automatically:
1. Analyze historical data
2. Generate strategy with insights
3. Create execution timeline with phases
4. **Generate creative prompts for each test combination** ← New!
5. Output campaign configuration with creative assets

### Viewing Creative Prompts

The CLI displays creative prompts inline:

```
[1] SHORT-TERM DISCOVERY
    Test Combinations (3):
      [35%] Meta + Millennials 25-34 + UGC-style lifestyle
           → Test authentic lifestyle imagery with aspirational messaging
           📸 Creative Brief:
              Visual: High-quality lifestyle photograph, 28-year-old woman...
              Copy: "Join 10,000+ women who transformed their mornings..."
              Headline: "Transform Your Mornings in 30 Days"
              CTA: SHOP_NOW
              Hooks: "What if your morning routine could change everything?" (+4 more)
              Specs: 1:1 | 1080x1080
```

At the end of the timeline:

```
📸 CREATIVE ASSETS SUMMARY:
  Total creative briefs generated: 6
  Platforms covered: Meta, TikTok
  Ready for AI image generation (DALL-E, Midjourney, etc.)
```

## Customization

### Brand Guidelines

Provide brand guidelines in your project to influence creative generation:

```python
# When creating project or uploading data
user_inputs = {
    "product_description": "30-day wellness program...",
    "brand_guidelines": """
        Brand Voice: Authentic, empowering, science-backed
        Visual Style: Natural lighting, real people, aspirational but relatable
        Color Palette: Warm earth tones, avoid neon/harsh colors
        Logo Placement: Bottom-right, subtle
        Avoid: Stock imagery, overly polished aesthetics
    """
}
```

This will be passed to the creative generator and influence:
- Visual prompt style descriptions
- Ad copy tone and messaging
- Technical specs (brand asset placement, color schemes)

### Platform Prioritization

The creative generator respects your strategy's platform priorities:

```json
{
  "platform_strategy": {
    "priorities": ["Meta", "TikTok"],
    "budget_split": {"Meta": 0.6, "TikTok": 0.4}
  }
}
```

Test combinations will be generated for prioritized platforms, with appropriate specs for each.

## Future Integrations

### 1. AI Image Generation

**Status**: Stub implemented in `src/integrations/image_generator.py`

**Planned workflow**:
```python
from src.integrations.image_generator import create_image_generator

# Initialize generator
generator = create_image_generator("dall-e", api_key=os.getenv("OPENAI_API_KEY"))

# Generate images for all creative assets
for asset in config["creative_assets"]:
    creative = asset["creative_generation"]

    image_url = generator.generate(
        prompt=creative["visual_prompt"],
        specs=creative["technical_specs"]
    )

    # Store image URL/hash for ad deployment
    asset["generated_image"] = image_url
```

**Supported providers** (when implemented):
- **DALL-E 3** (OpenAI): Highest quality, best for polished/professional
- **Midjourney**: Artistic style, best for lifestyle/aesthetic
- **Stable Diffusion**: Cost-effective, local deployment option

### 2. Meta Ads API Deployment

**Status**: Stub implemented in `src/integrations/meta_ads.py`

**Planned workflow**:
```python
from src.integrations.meta_ads import MetaAdsAPI

# Initialize Meta API
meta = MetaAdsAPI(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID")
)

# Automated campaign deployment
result = meta.create_campaign_from_config(config)

print(f"Campaign deployed!")
print(f"  Campaign ID: {result['campaign_id']}")
print(f"  Ad Set IDs: {result['ad_set_ids']}")
print(f"  Ad IDs: {result['ad_ids']}")
```

**Setup requirements**:
1. Create Meta App at https://developers.facebook.com/apps
2. Add Marketing API product
3. Generate access token with `ads_management` permission
4. Get ad account ID from Business Manager (format: `act_XXXXXXXXX`)

### 3. End-to-End Automation

**Future vision**:
```
Historical Data → Agent → Creative Prompts → Image Generation → Meta API → Live Campaign
                                ↓
                          Monitor Performance
                                ↓
                        Upload Experiment Results
                                ↓
                          Agent Optimization
                                ↓
                      Updated Campaign Configs
```

## API Reference

### `generate_creative_prompts()`

```python
def generate_creative_prompts(
    test_combination: Dict[str, Any],
    strategy: Dict[str, Any],
    user_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive creative prompts for a test combination

    Args:
        test_combination: Test combination from execution plan
            {
                "platform": "Meta",
                "audience": "Millennials 25-34",
                "creative": "UGC-style video",
                ...
            }
        strategy: Generated strategy with insights and recommendations
        user_inputs: User-provided context (product, brand guidelines, etc.)

    Returns:
        Dictionary with creative generation prompts:
        {
            "visual_prompt": "...",
            "copy_primary_text": "...",
            "copy_headline": "...",
            "copy_cta": "...",
            "hooks": [...],
            "technical_specs": {...}
        }
    """
```

### `validate_creative_prompt()`

```python
def validate_creative_prompt(
    creative_prompt: Dict[str, Any],
    platform: str
) -> Tuple[bool, List[str]]:
    """
    Validate creative prompt completeness and platform compliance

    Args:
        creative_prompt: Generated creative prompt dictionary
        platform: Target platform (Meta, TikTok, Google Ads)

    Returns:
        Tuple of (is_valid, error_messages)
    """
```

### `get_platform_specs_summary()`

```python
def get_platform_specs_summary(platform: str) -> str:
    """
    Get human-readable summary of platform specifications

    Args:
        platform: Target platform

    Returns:
        Formatted summary string with placements, copy limits, file requirements
    """
```

## Validation & Quality Control

### Automatic Validation

The system automatically validates each generated creative prompt:

✅ **Required fields present**
- visual_prompt
- copy_primary_text
- copy_headline
- copy_cta
- hooks (minimum 3)
- technical_specs

✅ **Platform compliance**
- Copy within character limits
- Dimensions match platform specs
- File format/size appropriate

✅ **Hook diversity**
- At least 3 hook variations
- Different psychological angles

### Manual Review

Review generated creative prompts in:
1. **CLI output**: Inline display during execution
2. **Campaign config file**: `campaign_{project_id}_v{iteration}.json`
3. **Supabase database**: `experiment_plan` column in `projects` table

## Best Practices

### 1. Provide Detailed Brand Guidelines

**Good**:
```
Brand Voice: Authentic, empowering, science-backed
Visual Style: Natural lighting, real people (18-35), morning settings, indoor/outdoor mix
Color Palette: Warm earth tones (#D4A574, #8B7355), white backgrounds
Logo: Subtle placement bottom-right, 10% opacity
Avoid: Stock imagery, models, overly polished aesthetics, gym settings
```

**Bad**:
```
Brand: Modern and professional
```

### 2. Use Specific Product Descriptions

**Good**:
```
30-day wellness program combining morning routines, nutrition guidance, and mindfulness practices. Target: busy professionals (25-40) seeking sustainable lifestyle changes. Price: $49/month. Key differentiator: Science-backed routines that fit in 15 minutes.
```

**Bad**:
```
Wellness program
```

### 3. Review & Iterate

- Generated prompts are **starting points**, not final assets
- Test multiple hooks to find winning angles
- Adjust visual prompts based on generated image quality
- Refine copy based on platform performance

### 4. Platform-Native Aesthetics

The system generates platform-appropriate creative:
- **TikTok**: Authentic, UGC-style, vertical video aesthetic
- **Meta**: Polished lifestyle, aspirational but relatable
- **Google**: Clean, informative, benefit-focused

Trust these defaults, but customize if your brand demands it.

## Troubleshooting

### "Creative generation failed for combo_X"

**Cause**: LLM call failed or returned invalid JSON

**Solution**:
1. Check Gemini API key is valid: `GEMINI_API_KEY` in `.env`
2. Review error message in logs
3. Re-run agent (failure on single combo won't block entire flow)
4. Manual creative development required for failed combos

### "Validation warnings: Primary text exceeds 125 character limit"

**Cause**: LLM generated copy exceeding platform limits

**Solution**:
- This is just a warning - creative is still included
- Manually trim copy before deploying to platform
- Or add to brand guidelines: "Keep copy under 100 characters"

### "No creative assets in campaign config"

**Cause**: Execution plan missing or has no test combinations

**Solution**:
1. Verify execution timeline was generated: check `experiment_plan` in state
2. Ensure test combinations have `creative_generation` field
3. Check logs for creative generation step

## Examples

### Example 1: E-commerce Product Launch

**Input**:
```
Product: Smart fitness tracker with sleep monitoring
Historical Data: Previous campaigns on Meta (CPA: $35) and Google (CPA: $42)
Budget: $1000/day
```

**Generated Creative** (for Meta + Health-conscious millennials + Product demo):
```
Visual Prompt: "Product photography style, sleek black fitness tracker on wrist,
close-up shot, person jogging in urban park setting, morning light, shallow depth
of field, focus on device screen showing sleep score '94', background slightly
blurred, modern active lifestyle aesthetic, clean composition 1:1 square format"

Copy: "Track your sleep, optimize your mornings. Smart insights that actually
improve your health. Join 50K+ users sleeping better."

Headline: "Sleep Better, Perform Better"

CTA: SHOP_NOW

Hooks:
1. "Your sleep score reveals everything about your health"
2. "Why top performers track their sleep obsessively"
3. "The $99 device that transformed my energy levels"
4. "Sleep tracking that actually helps you sleep better"
5. "50,000+ people are sleeping better - here's how"
```

### Example 2: SaaS B2B Tool

**Input**:
```
Product: Team collaboration software for remote teams
Historical Data: LinkedIn campaigns (CPA: $85), Google Search (CPA: $120)
Budget: $500/day
```

**Generated Creative** (for LinkedIn + Managers/Directors + Problem-solution):
```
Visual Prompt: "Professional B2B software interface screenshot, modern dashboard
on laptop screen, clean workspace setting, coffee cup nearby, natural window
light, organized desk, team collaboration view with colorful project boards,
1.91:1 wide format for LinkedIn feed, professional but not corporate, productive
work environment feel"

Copy: "Remote teams lose 2 hours/day to context switching. Our collaboration
platform cuts that in half. See why 500+ companies switched."

Headline: "Stop Losing Hours to Tool Switching"

CTA: LEARN_MORE

Hooks:
1. "Your team is wasting 10+ hours every week (here's how to stop it)"
2. "Why remote-first companies are ditching Slack"
3. "The collaboration tool that actually increased our productivity"
4. "500+ companies made the switch - here's what they learned"
5. "Remote work doesn't have to feel chaotic"
```

## Testing

Run creative generation tests:

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python tests/test_creative_generation.py
```

Test coverage:
- Platform specs structure
- Creative prompt validation (valid/invalid cases)
- Copy length limits enforcement
- Hook count requirements
- Technical specs structure
- Platform-specific compliance

## Roadmap

### Phase 1: Current (Implemented)
- ✅ LLM-powered creative prompt generation
- ✅ Platform-specific requirements
- ✅ Validation & quality control
- ✅ CLI display integration

### Phase 2: Image Generation (Q1 2025)
- 🔄 DALL-E 3 integration
- 🔄 Midjourney integration (when API available)
- 🔄 Stable Diffusion local/API support
- 🔄 Batch generation for all test combinations
- 🔄 Image quality scoring & filtering

### Phase 3: Meta Ads Deployment (Q2 2025)
- 🔄 Meta Marketing API integration
- 🔄 Automated campaign creation
- 🔄 Image upload to Ad Library
- 🔄 Ad creative & ad set management
- 🔄 Performance monitoring integration

### Phase 4: Full Automation (Q3 2025)
- 🔄 End-to-end workflow: data → strategy → creative → deployment
- 🔄 Real-time optimization based on performance
- 🔄 Multi-platform support (TikTok, Google Ads APIs)
- 🔄 A/B test automation (hook variations)
- 🔄 Creative fatigue detection & refresh

## Support

Questions or issues? Check:
1. This documentation
2. Code comments in `src/modules/creative_generator.py`
3. Example outputs in `campaign_*.json` files
4. Integration stubs in `src/integrations/`

## License

Part of Adronaut Agent - See repository LICENSE
