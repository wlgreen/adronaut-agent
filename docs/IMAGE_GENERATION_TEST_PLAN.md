# Comprehensive Image Generation Workflow Test Plan

## Overview

This test plan evaluates the complete image generation workflow (`test-creative` command) across diverse product types, platforms, creative styles, and complexity levels. The goal is to assess workflow quality, identify strengths/weaknesses, and provide actionable recommendations.

## Test Objectives

1. **Quality Assessment:** Evaluate prompt quality and generated image quality across 8 rating categories
2. **Success Rate Analysis:** Measure image generation success rate and failure patterns
3. **Platform Performance:** Compare workflow effectiveness across Meta, TikTok, and Google
4. **Feature Extraction Accuracy:** Validate product feature detection and visual marker mapping
5. **Edge Case Handling:** Test workflow robustness with challenging inputs
6. **Execution Performance:** Measure timing and resource usage

## Evaluation Metrics

### Prompt Quality Metrics (0-10 each):
- Keyword Presence
- Brand/Logo Visibility
- Prompt Adherence
- Visual Clarity
- Product Fidelity
- Professional Quality
- Completeness
- Authenticity
- **Overall Score:** 0-100

### Image Quality Metrics (0-10 each):
- Visual Quality
- Prompt Adherence
- Product Visibility
- Brand Presence
- Platform Fit
- Technical Quality

### Success Metrics:
- Image generation success rate (%)
- Steps completed successfully
- Execution time per step
- Total workflow time

---

## Test Cases (30 Total)

### Category 1: Electronics (3 cases)

#### TC-001: Wireless Headphones - Meta - Aspirational Lifestyle
**Product Description:** "Premium wireless headphones with active noise cancellation, 30-hour battery life, and studio-quality sound. Sleek matte black design with memory foam ear cushions and intuitive touch controls."

**Keywords:** "noise cancellation, wireless, premium, battery life"
**Brand:** "AudioTech"
**Platform:** Meta
**Creative Style:** Aspirational lifestyle
**Audience:** "Tech enthusiasts and professionals 25-40"
**Complexity:** Medium (multiple features)
**Expected Features:** Headphones visible, user wearing/using, professional setting, lifestyle context

---

#### TC-002: Smartphone - TikTok - Action/Dynamic
**Product Description:** "5G smartphone with 108MP triple camera system, 120Hz AMOLED display, and lightning-fast processor. Capture stunning photos and videos with AI-powered features."

**Keywords:** "5G, camera, AMOLED, AI"
**Brand:** "TechNova"
**Platform:** TikTok
**Creative Style:** Action/dynamic
**Audience:** "Gen Z content creators 18-28"
**Complexity:** Complex (technical features)
**Expected Features:** Phone in action, camera capabilities demonstrated, dynamic movement

---

#### TC-003: Smart Watch - Google - Product-Focused Minimal
**Product Description:** "Minimalist fitness smartwatch with heart rate monitoring, sleep tracking, and 7-day battery life. Water-resistant up to 50 meters."

**Keywords:** "fitness, heart rate, sleep tracking"
**Brand:** "FitTime"
**Platform:** Google
**Creative Style:** Product-focused minimal
**Audience:** "Fitness enthusiasts 25-45"
**Complexity:** Medium
**Expected Features:** Watch close-up, clean background, features visible on display

---

### Category 2: Fashion (3 cases)

#### TC-004: Running Shoes - Meta - Action/Dynamic
**Product Description:** "Ultra-lightweight running shoes with responsive cushioning and breathable mesh upper. Engineered for speed with carbon fiber plate and grippy outsole."

**Keywords:** "running, lightweight, cushioning, breathable"
**Brand:** "VeloRun"
**Platform:** Meta
**Creative Style:** Action/dynamic
**Audience:** "Runners and fitness enthusiasts 20-40"
**Complexity:** Medium
**Expected Features:** Shoes on runner in motion, outdoor setting, action shot

---

#### TC-005: Designer Sunglasses - TikTok - Aspirational Lifestyle
**Product Description:** "Polarized aviator sunglasses with titanium frame and gradient lenses. Timeless style meets modern UV protection."

**Keywords:** "polarized, aviator, UV protection"
**Brand:** "LuxVision"
**Platform:** TikTok
**Creative Style:** Aspirational lifestyle
**Audience:** "Fashion-conscious millennials 25-35"
**Complexity:** Simple (single product)
**Expected Features:** Person wearing sunglasses, stylish setting, lifestyle context

---

#### TC-006: Leather Jacket - Google - Emotional Storytelling
**Product Description:** "Hand-crafted genuine leather jacket with vintage patina and classic biker silhouette. Premium full-grain leather ages beautifully with wear."

**Keywords:** "leather, handcrafted, vintage, premium"
**Brand:** "Heritage & Co"
**Platform:** Google
**Creative Style:** Emotional storytelling
**Audience:** "Style-conscious men 30-50"
**Complexity:** Medium
**Expected Features:** Jacket worn in authentic setting, storytelling elements, craftsmanship details

---

### Category 3: Food & Beverage (3 cases)

#### TC-007: Organic Coffee - Meta - Product-Focused Minimal
**Product Description:** "Single-origin organic coffee beans from Ethiopian highlands. Medium roast with notes of blueberry, chocolate, and citrus. Fair trade certified."

**Keywords:** "organic, single-origin, fair trade, Ethiopian"
**Brand:** "PeakBean"
**Platform:** Meta
**Creative Style:** Product-focused minimal
**Audience:** "Coffee enthusiasts 25-45"
**Complexity:** Medium
**Expected Features:** Coffee bag/beans prominently displayed, minimal clean background

---

#### TC-008: Energy Drink - TikTok - Action/Dynamic
**Product Description:** "Zero-sugar energy drink with natural caffeine from green tea, B vitamins, and electrolytes. Refreshing citrus flavor powers your workout and workday."

**Keywords:** "energy, zero-sugar, natural caffeine, electrolytes"
**Brand:** "PowerSurge"
**Platform:** TikTok
**Creative Style:** Action/dynamic
**Audience:** "Active young adults 18-30"
**Complexity:** Medium
**Expected Features:** Can in action, athletic/active setting, energy/movement

---

#### TC-009: Craft Beer - Google - Emotional Storytelling
**Product Description:** "Award-winning IPA brewed with Cascade and Citra hops. Bold tropical flavors with citrus finish. Small-batch craft brewing tradition since 1995."

**Keywords:** "craft, IPA, hops, small-batch"
**Brand:** "Hopworks Brewery"
**Platform:** Google
**Creative Style:** Emotional storytelling
**Audience:** "Craft beer lovers 28-50"
**Complexity:** Medium
**Expected Features:** Beer bottle/glass, craft brewing atmosphere, heritage elements

---

### Category 4: Beauty & Skincare (3 cases)

#### TC-010: Anti-Aging Serum - Meta - Educational/Informative
**Product Description:** "Retinol serum with hyaluronic acid and vitamin C reduces fine lines and wrinkles. Clinically proven to improve skin texture in 4 weeks."

**Keywords:** "retinol, anti-aging, hyaluronic acid, clinically proven"
**Brand:** "DermaLux"
**Platform:** Meta
**Creative Style:** Educational/informative
**Audience:** "Women 35-55 interested in skincare"
**Complexity:** Medium (scientific/clinical)
**Expected Features:** Product bottle, ingredient callouts, before/after suggestion

---

#### TC-011: Lipstick - TikTok - Product-Focused Minimal
**Product Description:** "Long-lasting matte lipstick in bold red shade. Enriched with shea butter and vitamin E for all-day comfort. Vegan and cruelty-free."

**Keywords:** "matte, long-lasting, vegan, cruelty-free"
**Brand:** "ColorTrue"
**Platform:** TikTok
**Creative Style:** Product-focused minimal
**Audience:** "Beauty enthusiasts 18-35"
**Complexity:** Simple
**Expected Features:** Lipstick tube and color swatch, clean minimal background

---

#### TC-012: Face Moisturizer - Google - Comparison/Before-After
**Product Description:** "Hydrating face cream with ceramides and niacinamide. Restores skin barrier and provides 24-hour moisture for dry sensitive skin."

**Keywords:** "hydrating, ceramides, niacinamide, sensitive skin"
**Brand:** "SkinBalance"
**Platform:** Google
**Creative Style:** Comparison/before-after
**Audience:** "Adults 25-50 with dry skin"
**Complexity:** Medium
**Expected Features:** Product jar, skin transformation concept, clinical feel

---

### Category 5: Home Goods (3 cases)

#### TC-013: Smart Thermostat - Meta - Educational/Informative
**Product Description:** "WiFi-enabled smart thermostat learns your schedule and preferences. Save up to 23% on energy bills with intelligent temperature control and smartphone app."

**Keywords:** "smart, WiFi, energy savings, app-controlled"
**Brand:** "EcoTemp"
**Platform:** Meta
**Creative Style:** Educational/informative
**Audience:** "Homeowners 30-55"
**Complexity:** Complex (technical + benefits)
**Expected Features:** Thermostat on wall, home setting, tech/savings indicators

---

#### TC-014: Standing Desk - TikTok - Comparison/Before-After
**Product Description:** "Electric height-adjustable standing desk with memory presets. Solid bamboo desktop and whisper-quiet motor. Transform your workspace for better health."

**Keywords:** "standing desk, adjustable, electric, bamboo"
**Brand:** "DeskRise"
**Platform:** TikTok
**Creative Style:** Comparison/before-after
**Audience:** "Remote workers and office workers 25-45"
**Complexity:** Medium
**Expected Features:** Desk in use, height adjustment shown, workspace transformation

---

#### TC-015: Air Purifier - Google - Product-Focused Minimal
**Product Description:** "HEPA air purifier removes 99.97% of allergens, dust, and pet dander. Quiet operation for bedroom or office. Smart sensor adjusts fan speed automatically."

**Keywords:** "HEPA, air purifier, allergens, smart sensor"
**Brand:** "PureAir Pro"
**Platform:** Google
**Creative Style:** Product-focused minimal
**Audience:** "Health-conscious adults 30-60"
**Complexity:** Medium
**Expected Features:** Purifier unit, clean air concept, minimal setting

---

### Category 6: Services & Digital Products (3 cases)

#### TC-016: Meditation App - Meta - Emotional Storytelling
**Product Description:** "Meditation and mindfulness app with guided sessions, sleep stories, and breathing exercises. Reduce stress and improve focus with 10 minutes daily practice."

**Keywords:** "meditation, mindfulness, stress reduction, sleep"
**Brand:** "CalmPath"
**Platform:** Meta
**Creative Style:** Emotional storytelling
**Audience:** "Stressed professionals 25-45"
**Complexity:** Abstract (intangible service)
**Expected Features:** Person meditating, peaceful setting, app interface hint

---

#### TC-017: Online Coding Course - TikTok - Educational/Informative
**Product Description:** "Learn Python programming from zero to job-ready in 12 weeks. Interactive coding challenges, real-world projects, and career support. No prior experience needed."

**Keywords:** "Python, coding, programming, career"
**Brand:** "CodeAcademy Pro"
**Platform:** TikTok
**Creative Style:** Educational/informative
**Audience:** "Career changers 22-40"
**Complexity:** Abstract (education service)
**Expected Features:** Person coding/learning, laptop visible, success concept

---

#### TC-018: Cloud Storage Service - Google - Comparison/Before-After
**Product Description:** "Secure cloud storage with 2TB space, automatic backup, and file sharing. Access your files anywhere with military-grade encryption and 99.9% uptime."

**Keywords:** "cloud storage, backup, secure, encryption"
**Brand:** "CloudVault"
**Platform:** Google
**Creative Style:** Comparison/before-after
**Audience:** "Business professionals 30-55"
**Complexity:** Abstract (digital service)
**Expected Features:** Data organization concept, security visual, cloud metaphor

---

### Category 7: Sports & Fitness (3 cases)

#### TC-019: Yoga Mat - Meta - Aspirational Lifestyle
**Product Description:** "Premium non-slip yoga mat with extra cushioning and eco-friendly natural rubber. Includes carrying strap. Perfect for hot yoga and intense workouts."

**Keywords:** "yoga, non-slip, eco-friendly, cushioning"
**Brand:** "ZenFlow"
**Platform:** Meta
**Creative Style:** Aspirational lifestyle
**Audience:** "Yoga practitioners 25-45"
**Complexity:** Simple
**Expected Features:** Person doing yoga on mat, studio/outdoor setting, lifestyle

---

#### TC-020: Protein Powder - TikTok - Action/Dynamic
**Product Description:** "Whey protein isolate with 25g protein per serving. Chocolate flavor with no artificial sweeteners. Supports muscle recovery and growth after intense training."

**Keywords:** "protein, whey isolate, muscle recovery, no artificial sweeteners"
**Brand:** "MaxGain"
**Platform:** TikTok
**Creative Style:** Action/dynamic
**Audience:** "Gym-goers and athletes 20-40"
**Complexity:** Medium
**Expected Features:** Protein container, athletic setting, action/workout context

---

#### TC-021: Resistance Bands - Google - Educational/Informative
**Product Description:** "Set of 5 resistance bands with different tension levels from 10-50 lbs. Includes door anchor, handles, and ankle straps. Full-body workout anywhere."

**Keywords:** "resistance bands, workout, full-body, portable"
**Brand:** "FitBands Pro"
**Platform:** Google
**Creative Style:** Educational/informative
**Audience:** "Home fitness enthusiasts 25-50"
**Complexity:** Simple
**Expected Features:** Bands and accessories displayed, workout demonstration

---

### Category 8: Automotive (3 cases)

#### TC-022: Car Wax - Meta - Product-Focused Minimal
**Product Description:** "Premium carnauba car wax provides mirror-like shine and protection for up to 6 months. Easy application with microfiber applicator included."

**Keywords:** "car wax, carnauba, shine, protection"
**Brand:** "AutoGlow"
**Platform:** Meta
**Creative Style:** Product-focused minimal
**Audience:** "Car enthusiasts 25-55"
**Complexity:** Simple
**Expected Features:** Wax container, shiny car surface, product close-up

---

#### TC-023: Dash Cam - TikTok - Educational/Informative
**Product Description:** "4K dash cam with night vision, GPS, and parking mode. Loop recording with G-sensor for accident detection. Protect yourself with clear evidence."

**Keywords:** "dash cam, 4K, night vision, GPS"
**Brand:** "RoadGuard"
**Platform:** TikTok
**Creative Style:** Educational/informative
**Audience:** "Drivers 25-50"
**Complexity:** Complex (technical features)
**Expected Features:** Dash cam installed, road view, security concept

---

#### TC-024: Car Phone Mount - Google - Product-Focused Minimal
**Product Description:** "Magnetic car phone mount with 360-degree rotation and strong grip. One-handed operation. Compatible with all smartphones and cases."

**Keywords:** "car mount, magnetic, 360-degree, universal"
**Brand:** "DriveSafe"
**Platform:** Google
**Creative Style:** Product-focused minimal
**Audience:** "Drivers 20-50"
**Complexity:** Simple
**Expected Features:** Mount with phone, car interior, clean shot

---

### Category 9: Health & Wellness (3 cases)

#### TC-025: Vitamins - Meta - Comparison/Before-After
**Product Description:** "Daily multivitamin with 23 essential nutrients including vitamin D3, B12, and zinc. Supports immune health, energy, and overall wellness. Non-GMO and gluten-free."

**Keywords:** "multivitamin, immune health, energy, non-GMO"
**Brand:** "VitalLife"
**Platform:** Meta
**Creative Style:** Comparison/before-after
**Audience:** "Health-conscious adults 30-60"
**Complexity:** Medium
**Expected Features:** Vitamin bottle, health transformation concept, wellness imagery

---

#### TC-026: Sleep Aid Supplement - TikTok - Emotional Storytelling
**Product Description:** "Natural sleep supplement with melatonin, magnesium, and L-theanine. Fall asleep faster and wake refreshed without grogginess. Drug-free formula."

**Keywords:** "sleep, melatonin, natural, drug-free"
**Brand:** "RestWell"
**Platform:** TikTok
**Creative Style:** Emotional storytelling
**Audience:** "Adults with sleep issues 25-55"
**Complexity:** Medium
**Expected Features:** Person sleeping peacefully, bedtime setting, relaxation mood

---

#### TC-027: Posture Corrector - Google - Educational/Informative
**Product Description:** "Adjustable posture corrector brace relieves back and neck pain. Breathable design for all-day wear. Improve posture and confidence."

**Keywords:** "posture corrector, back pain relief, adjustable"
**Brand:** "BackAlign"
**Platform:** Google
**Creative Style:** Educational/informative
**Audience:** "Office workers and adults 25-55"
**Complexity:** Medium
**Expected Features:** Person wearing brace, posture improvement shown, comfort

---

### Category 10: Luxury & Premium (3 cases - Edge Cases)

#### TC-028: Designer Watch - Meta - Aspirational Lifestyle
**Product Description:** "Swiss automatic watch with sapphire crystal, stainless steel case, and genuine leather strap. Precision movement with 48-hour power reserve. Timeless elegance for the modern gentleman."

**Keywords:** "Swiss, automatic, sapphire crystal, leather"
**Brand:** "Chronos Elite"
**Platform:** Meta
**Creative Style:** Aspirational lifestyle
**Audience:** "Affluent professionals 35-60"
**Complexity:** Complex (luxury + technical)
**Expected Features:** Watch close-up, luxury setting, worn on wrist, craftsmanship

---

#### TC-029: Premium Fountain Pen - TikTok - Product-Focused Minimal
**Product Description:** "Handcrafted fountain pen with 18K gold nib and ebonite body. Smooth writing experience with included converter for bottled ink. Collector's edition with serial number."

**Keywords:** "fountain pen, handcrafted, gold nib, collector's edition"
**Brand:** "Inkwell Luxury"
**Platform:** TikTok
**Creative Style:** Product-focused minimal
**Audience:** "Writing enthusiasts and collectors 30-65"
**Complexity:** Medium (niche product)
**Expected Features:** Pen close-up, writing in action, craftsmanship details

---

#### TC-030: Champagne - Google - Emotional Storytelling (EDGE CASE: Alcohol)
**Product Description:** "Vintage champagne from French vineyards with delicate bubbles and notes of brioche and green apple. Perfect for celebrations and special moments."

**Keywords:** "champagne, vintage, French, celebration"
**Brand:** "Château Élégance"
**Platform:** Google
**Creative Style:** Emotional storytelling
**Audience:** "Wine enthusiasts 30-60"
**Complexity:** Medium (regulated product)
**Expected Features:** Champagne bottle/glass, celebration setting, elegance, luxury

---

## Test Execution Protocol

### Automated Execution:
1. Run all 30 test cases using bash script
2. Save outputs to `output/test_results/` with naming: `TC-XXX_<product>_<platform>.json`
3. Save generated images to `output/test_results/images/`
4. Track execution time and success/failure for each test

### Manual Review:
1. Visual inspection of all 30 generated images
2. Verification of platform compliance
3. Validation of feature extraction accuracy
4. Review of rating consistency

---

## Success Criteria

### Minimum Acceptable Performance:
- **Image Generation Success Rate:** ≥ 90% (27/30 cases)
- **Average Prompt Quality Score:** ≥ 75/100
- **Average Image Quality Score:** ≥ 70/100
- **Feature Extraction Accuracy:** ≥ 80% (features correctly identified)
- **Platform Compliance:** 100% (all outputs meet platform specs)

### Excellence Targets:
- **Image Generation Success Rate:** 100% (30/30 cases)
- **Average Prompt Quality Score:** ≥ 85/100
- **Average Image Quality Score:** ≥ 80/100
- **Feature Extraction Accuracy:** ≥ 95%
- **Execution Time:** < 60 seconds per test case

---

## Analysis Plan

### Quantitative Analysis:
1. **Overall Statistics:**
   - Success rate, average scores, standard deviation
   - Execution time metrics (mean, median, min, max)

2. **Platform Comparison:**
   - Average scores by platform (Meta vs TikTok vs Google)
   - Success rate by platform
   - Image quality differences by aspect ratio

3. **Creative Style Performance:**
   - Score distribution across 6 creative styles
   - Best/worst performing styles

4. **Complexity Analysis:**
   - Simple vs Medium vs Complex vs Abstract
   - Edge case performance

5. **Feature Extraction:**
   - Accuracy rate across product categories
   - Common extraction errors

### Qualitative Analysis:
1. Visual quality assessment of generated images
2. Prompt adherence evaluation
3. Brand presence consistency
4. Platform appropriateness
5. Common failure patterns

### Correlation Analysis:
- Prompt quality score vs image quality score
- Product complexity vs execution time
- Creative style vs success rate
- Platform vs image quality

---

## Report Structure

### Final Evaluation Report Contents:
1. **Executive Summary**
2. **Test Execution Overview** (30 cases, success rate, timing)
3. **Quantitative Results** (tables, statistics)
4. **Platform Performance Analysis** (Meta/TikTok/Google comparison)
5. **Creative Style Analysis** (which styles work best)
6. **Quality Assessment** (prompt and image quality deep-dive)
7. **Feature Extraction Review** (accuracy and issues)
8. **Failure Analysis** (patterns, root causes)
9. **Strengths & Weaknesses** (what works, what doesn't)
10. **Recommendations** (specific improvements)
11. **Appendices** (all test case details, raw data)

---

## Timeline

- **Test Plan Document:** 30 minutes
- **Automation Script:** 15 minutes
- **Test Execution:** ~30 minutes (30 tests × ~60 sec each)
- **Analysis:** 45 minutes
- **Report Writing:** 45 minutes

**Total Estimated Time:** ~2.5 hours
