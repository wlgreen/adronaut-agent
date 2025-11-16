#!/bin/bash

# Image Generation Workflow Test Automation Script
# Executes all 30 test cases from IMAGE_GENERATION_TEST_PLAN.md

# Activate virtual environment
source venv/bin/activate

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directories
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="output/test_results/${TIMESTAMP}"
IMAGES_DIR="${OUTPUT_DIR}/images"
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${IMAGES_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Image Generation Workflow Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Output directory: ${OUTPUT_DIR}\n"

# Track results
TOTAL_TESTS=30
PASSED=0
FAILED=0
START_TIME=$(date +%s)

# Test execution function
run_test() {
    local test_id=$1
    local product_desc=$2
    local keywords=$3
    local brand=$4
    local platform=$5
    local style=$6
    local audience=$7
    local product_name=$8

    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running ${test_id}: ${product_name} (${platform})${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local output_file="${OUTPUT_DIR}/${test_id}_$(echo ${product_name} | tr ' ' '_')_${platform}.json"
    local test_start=$(date +%s)

    # Run test-creative command
    if python cli.py test-creative \
        --product-description "${product_desc}" \
        --platform "${platform}" \
        --keywords "${keywords}" \
        --brand-name "${brand}" \
        --creative-style "${style}" \
        --audience "${audience}" \
        --output "${output_file}"; then

        local test_end=$(date +%s)
        local duration=$((test_end - test_start))

        echo -e "${GREEN}✓ ${test_id} PASSED${NC} (${duration}s)"
        PASSED=$((PASSED + 1))

        # Move generated image if exists
        if [ -f "$(dirname ${output_file})/images/$(basename ${output_file} .json).png" ]; then
            mv "$(dirname ${output_file})/images/$(basename ${output_file} .json).png" "${IMAGES_DIR}/${test_id}_${product_name// /_}.png" 2>/dev/null || true
        fi
    else
        echo -e "${RED}✗ ${test_id} FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# Execute all 30 test cases

echo -e "\n${BLUE}Category 1: Electronics${NC}"

# TC-001
run_test "TC-001" \
    "Premium wireless headphones with active noise cancellation, 30-hour battery life, and studio-quality sound. Sleek matte black design with memory foam ear cushions and intuitive touch controls." \
    "noise cancellation,wireless,premium,battery life" \
    "AudioTech" \
    "Meta" \
    "Aspirational lifestyle" \
    "Tech enthusiasts and professionals 25-40" \
    "Wireless_Headphones"

# TC-002
run_test "TC-002" \
    "5G smartphone with 108MP triple camera system, 120Hz AMOLED display, and lightning-fast processor. Capture stunning photos and videos with AI-powered features." \
    "5G,camera,AMOLED,AI" \
    "TechNova" \
    "TikTok" \
    "Action/dynamic" \
    "Gen Z content creators 18-28" \
    "Smartphone"

# TC-003
run_test "TC-003" \
    "Minimalist fitness smartwatch with heart rate monitoring, sleep tracking, and 7-day battery life. Water-resistant up to 50 meters." \
    "fitness,heart rate,sleep tracking" \
    "FitTime" \
    "Google" \
    "Product-focused minimal" \
    "Fitness enthusiasts 25-45" \
    "Smart_Watch"

echo -e "\n${BLUE}Category 2: Fashion${NC}"

# TC-004
run_test "TC-004" \
    "Ultra-lightweight running shoes with responsive cushioning and breathable mesh upper. Engineered for speed with carbon fiber plate and grippy outsole." \
    "running,lightweight,cushioning,breathable" \
    "VeloRun" \
    "Meta" \
    "Action/dynamic" \
    "Runners and fitness enthusiasts 20-40" \
    "Running_Shoes"

# TC-005
run_test "TC-005" \
    "Polarized aviator sunglasses with titanium frame and gradient lenses. Timeless style meets modern UV protection." \
    "polarized,aviator,UV protection" \
    "LuxVision" \
    "TikTok" \
    "Aspirational lifestyle" \
    "Fashion-conscious millennials 25-35" \
    "Designer_Sunglasses"

# TC-006
run_test "TC-006" \
    "Hand-crafted genuine leather jacket with vintage patina and classic biker silhouette. Premium full-grain leather ages beautifully with wear." \
    "leather,handcrafted,vintage,premium" \
    "Heritage & Co" \
    "Google" \
    "Emotional storytelling" \
    "Style-conscious men 30-50" \
    "Leather_Jacket"

echo -e "\n${BLUE}Category 3: Food & Beverage${NC}"

# TC-007
run_test "TC-007" \
    "Single-origin organic coffee beans from Ethiopian highlands. Medium roast with notes of blueberry, chocolate, and citrus. Fair trade certified." \
    "organic,single-origin,fair trade,Ethiopian" \
    "PeakBean" \
    "Meta" \
    "Product-focused minimal" \
    "Coffee enthusiasts 25-45" \
    "Organic_Coffee"

# TC-008
run_test "TC-008" \
    "Zero-sugar energy drink with natural caffeine from green tea, B vitamins, and electrolytes. Refreshing citrus flavor powers your workout and workday." \
    "energy,zero-sugar,natural caffeine,electrolytes" \
    "PowerSurge" \
    "TikTok" \
    "Action/dynamic" \
    "Active young adults 18-30" \
    "Energy_Drink"

# TC-009
run_test "TC-009" \
    "Award-winning IPA brewed with Cascade and Citra hops. Bold tropical flavors with citrus finish. Small-batch craft brewing tradition since 1995." \
    "craft,IPA,hops,small-batch" \
    "Hopworks Brewery" \
    "Google" \
    "Emotional storytelling" \
    "Craft beer lovers 28-50" \
    "Craft_Beer"

echo -e "\n${BLUE}Category 4: Beauty & Skincare${NC}"

# TC-010
run_test "TC-010" \
    "Retinol serum with hyaluronic acid and vitamin C reduces fine lines and wrinkles. Clinically proven to improve skin texture in 4 weeks." \
    "retinol,anti-aging,hyaluronic acid,clinically proven" \
    "DermaLux" \
    "Meta" \
    "Educational/informative" \
    "Women 35-55 interested in skincare" \
    "Anti_Aging_Serum"

# TC-011
run_test "TC-011" \
    "Long-lasting matte lipstick in bold red shade. Enriched with shea butter and vitamin E for all-day comfort. Vegan and cruelty-free." \
    "matte,long-lasting,vegan,cruelty-free" \
    "ColorTrue" \
    "TikTok" \
    "Product-focused minimal" \
    "Beauty enthusiasts 18-35" \
    "Lipstick"

# TC-012
run_test "TC-012" \
    "Hydrating face cream with ceramides and niacinamide. Restores skin barrier and provides 24-hour moisture for dry sensitive skin." \
    "hydrating,ceramides,niacinamide,sensitive skin" \
    "SkinBalance" \
    "Google" \
    "Comparison/before-after" \
    "Adults 25-50 with dry skin" \
    "Face_Moisturizer"

echo -e "\n${BLUE}Category 5: Home Goods${NC}"

# TC-013
run_test "TC-013" \
    "WiFi-enabled smart thermostat learns your schedule and preferences. Save up to 23% on energy bills with intelligent temperature control and smartphone app." \
    "smart,WiFi,energy savings,app-controlled" \
    "EcoTemp" \
    "Meta" \
    "Educational/informative" \
    "Homeowners 30-55" \
    "Smart_Thermostat"

# TC-014
run_test "TC-014" \
    "Electric height-adjustable standing desk with memory presets. Solid bamboo desktop and whisper-quiet motor. Transform your workspace for better health." \
    "standing desk,adjustable,electric,bamboo" \
    "DeskRise" \
    "TikTok" \
    "Comparison/before-after" \
    "Remote workers and office workers 25-45" \
    "Standing_Desk"

# TC-015
run_test "TC-015" \
    "HEPA air purifier removes 99.97% of allergens, dust, and pet dander. Quiet operation for bedroom or office. Smart sensor adjusts fan speed automatically." \
    "HEPA,air purifier,allergens,smart sensor" \
    "PureAir Pro" \
    "Google" \
    "Product-focused minimal" \
    "Health-conscious adults 30-60" \
    "Air_Purifier"

echo -e "\n${BLUE}Category 6: Services & Digital Products${NC}"

# TC-016
run_test "TC-016" \
    "Meditation and mindfulness app with guided sessions, sleep stories, and breathing exercises. Reduce stress and improve focus with 10 minutes daily practice." \
    "meditation,mindfulness,stress reduction,sleep" \
    "CalmPath" \
    "Meta" \
    "Emotional storytelling" \
    "Stressed professionals 25-45" \
    "Meditation_App"

# TC-017
run_test "TC-017" \
    "Learn Python programming from zero to job-ready in 12 weeks. Interactive coding challenges, real-world projects, and career support. No prior experience needed." \
    "Python,coding,programming,career" \
    "CodeAcademy Pro" \
    "TikTok" \
    "Educational/informative" \
    "Career changers 22-40" \
    "Online_Coding_Course"

# TC-018
run_test "TC-018" \
    "Secure cloud storage with 2TB space, automatic backup, and file sharing. Access your files anywhere with military-grade encryption and 99.9% uptime." \
    "cloud storage,backup,secure,encryption" \
    "CloudVault" \
    "Google" \
    "Comparison/before-after" \
    "Business professionals 30-55" \
    "Cloud_Storage_Service"

echo -e "\n${BLUE}Category 7: Sports & Fitness${NC}"

# TC-019
run_test "TC-019" \
    "Premium non-slip yoga mat with extra cushioning and eco-friendly natural rubber. Includes carrying strap. Perfect for hot yoga and intense workouts." \
    "yoga,non-slip,eco-friendly,cushioning" \
    "ZenFlow" \
    "Meta" \
    "Aspirational lifestyle" \
    "Yoga practitioners 25-45" \
    "Yoga_Mat"

# TC-020
run_test "TC-020" \
    "Whey protein isolate with 25g protein per serving. Chocolate flavor with no artificial sweeteners. Supports muscle recovery and growth after intense training." \
    "protein,whey isolate,muscle recovery,no artificial sweeteners" \
    "MaxGain" \
    "TikTok" \
    "Action/dynamic" \
    "Gym-goers and athletes 20-40" \
    "Protein_Powder"

# TC-021
run_test "TC-021" \
    "Set of 5 resistance bands with different tension levels from 10-50 lbs. Includes door anchor, handles, and ankle straps. Full-body workout anywhere." \
    "resistance bands,workout,full-body,portable" \
    "FitBands Pro" \
    "Google" \
    "Educational/informative" \
    "Home fitness enthusiasts 25-50" \
    "Resistance_Bands"

echo -e "\n${BLUE}Category 8: Automotive${NC}"

# TC-022
run_test "TC-022" \
    "Premium carnauba car wax provides mirror-like shine and protection for up to 6 months. Easy application with microfiber applicator included." \
    "car wax,carnauba,shine,protection" \
    "AutoGlow" \
    "Meta" \
    "Product-focused minimal" \
    "Car enthusiasts 25-55" \
    "Car_Wax"

# TC-023
run_test "TC-023" \
    "4K dash cam with night vision, GPS, and parking mode. Loop recording with G-sensor for accident detection. Protect yourself with clear evidence." \
    "dash cam,4K,night vision,GPS" \
    "RoadGuard" \
    "TikTok" \
    "Educational/informative" \
    "Drivers 25-50" \
    "Dash_Cam"

# TC-024
run_test "TC-024" \
    "Magnetic car phone mount with 360-degree rotation and strong grip. One-handed operation. Compatible with all smartphones and cases." \
    "car mount,magnetic,360-degree,universal" \
    "DriveSafe" \
    "Google" \
    "Product-focused minimal" \
    "Drivers 20-50" \
    "Car_Phone_Mount"

echo -e "\n${BLUE}Category 9: Health & Wellness${NC}"

# TC-025
run_test "TC-025" \
    "Daily multivitamin with 23 essential nutrients including vitamin D3, B12, and zinc. Supports immune health, energy, and overall wellness. Non-GMO and gluten-free." \
    "multivitamin,immune health,energy,non-GMO" \
    "VitalLife" \
    "Meta" \
    "Comparison/before-after" \
    "Health-conscious adults 30-60" \
    "Vitamins"

# TC-026
run_test "TC-026" \
    "Natural sleep supplement with melatonin, magnesium, and L-theanine. Fall asleep faster and wake refreshed without grogginess. Drug-free formula." \
    "sleep,melatonin,natural,drug-free" \
    "RestWell" \
    "TikTok" \
    "Emotional storytelling" \
    "Adults with sleep issues 25-55" \
    "Sleep_Aid_Supplement"

# TC-027
run_test "TC-027" \
    "Adjustable posture corrector brace relieves back and neck pain. Breathable design for all-day wear. Improve posture and confidence." \
    "posture corrector,back pain relief,adjustable" \
    "BackAlign" \
    "Google" \
    "Educational/informative" \
    "Office workers and adults 25-55" \
    "Posture_Corrector"

echo -e "\n${BLUE}Category 10: Luxury & Premium (Edge Cases)${NC}"

# TC-028
run_test "TC-028" \
    "Swiss automatic watch with sapphire crystal, stainless steel case, and genuine leather strap. Precision movement with 48-hour power reserve. Timeless elegance for the modern gentleman." \
    "Swiss,automatic,sapphire crystal,leather" \
    "Chronos Elite" \
    "Meta" \
    "Aspirational lifestyle" \
    "Affluent professionals 35-60" \
    "Designer_Watch"

# TC-029
run_test "TC-029" \
    "Handcrafted fountain pen with 18K gold nib and ebonite body. Smooth writing experience with included converter for bottled ink. Collector's edition with serial number." \
    "fountain pen,handcrafted,gold nib,collector's edition" \
    "Inkwell Luxury" \
    "TikTok" \
    "Product-focused minimal" \
    "Writing enthusiasts and collectors 30-65" \
    "Premium_Fountain_Pen"

# TC-030
run_test "TC-030" \
    "Vintage champagne from French vineyards with delicate bubbles and notes of brioche and green apple. Perfect for celebrations and special moments." \
    "champagne,vintage,French,celebration" \
    "Château Élégance" \
    "Google" \
    "Emotional storytelling" \
    "Wine enthusiasts 30-60" \
    "Champagne"

# Calculate final results
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
SUCCESS_RATE=$((PASSED * 100 / TOTAL_TESTS))

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Execution Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Tests:    ${TOTAL_TESTS}"
echo -e "${GREEN}Passed:         ${PASSED}${NC}"
echo -e "${RED}Failed:         ${FAILED}${NC}"
echo -e "Success Rate:   ${SUCCESS_RATE}%"
echo -e "Total Time:     ${TOTAL_TIME}s ($((TOTAL_TIME / 60))m $((TOTAL_TIME % 60))s)"
echo -e "Average Time:   $((TOTAL_TIME / TOTAL_TESTS))s per test"
echo -e "\nResults saved to: ${OUTPUT_DIR}"
echo -e "Images saved to: ${IMAGES_DIR}\n"

# Create summary file
SUMMARY_FILE="${OUTPUT_DIR}/test_summary.txt"
cat > "${SUMMARY_FILE}" << EOF
Image Generation Workflow Test Suite - Execution Summary
========================================

Execution Date: $(date)
Total Tests: ${TOTAL_TESTS}
Passed: ${PASSED}
Failed: ${FAILED}
Success Rate: ${SUCCESS_RATE}%
Total Execution Time: ${TOTAL_TIME}s ($((TOTAL_TIME / 60))m $((TOTAL_TIME % 60))s)
Average Time per Test: $((TOTAL_TIME / TOTAL_TESTS))s

Output Directory: ${OUTPUT_DIR}
Images Directory: ${IMAGES_DIR}

Test Plan: docs/IMAGE_GENERATION_TEST_PLAN.md
EOF

echo -e "Summary saved to: ${SUMMARY_FILE}\n"

if [ ${FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed successfully!${NC}\n"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Review the output above for details.${NC}\n"
    exit 1
fi
