#!/bin/bash
# Quick test script for the Room Detection API

API_URL="http://localhost:8000"

echo "=== Testing Room Detection API ==="
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

# Test 2: Simple floorplan
echo "2. Testing simple floorplan..."
curl -s -X POST "$API_URL/detect-rooms" \
  -H "Content-Type: application/json" \
  -d @tests/sample_data/test_floorplan.json | python3 -m json.tool
echo ""

# Test 3: L-shaped floorplan
echo "3. Testing L-shaped floorplan..."
curl -s -X POST "$API_URL/detect-rooms" \
  -H "Content-Type: application/json" \
  -d @tests/sample_data/test_l_shape_floorplan.json | python3 -m json.tool
echo ""

# Test 4: Pre-configured simple test
echo "4. Testing pre-configured simple endpoint..."
curl -s "$API_URL/test/simple" | python3 -m json.tool
echo ""

echo "=== Tests complete ==="
