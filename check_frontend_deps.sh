#!/bin/bash
# =============================================================================
# Frontend Dependency Verification Script
# =============================================================================
# Run this from any directory on the corporate network.
# It checks whether Node.js, npm, and all required frontend packages
# are available and installable.
#
# Usage:
#   chmod +x check_frontend_deps.sh
#   ./check_frontend_deps.sh
#
# Or just copy and paste the commands into your terminal.
# =============================================================================

echo "============================================="
echo "  FRONTEND DEPENDENCY VERIFICATION"
echo "============================================="
echo ""

# ----- SECTION 1: Runtime and Package Manager -----
echo "--- 1. Runtime & Package Manager ---"
echo ""

echo "Node.js version (need 18+):"
node --version 2>/dev/null || echo "  ERROR: Node.js is NOT installed"
echo ""

echo "npm version:"
npm --version 2>/dev/null || echo "  ERROR: npm is NOT installed"
echo ""

echo "npm registry URL (confirm it points to a reachable registry):"
npm config get registry
echo ""

# ----- SECTION 2: npm Registry Connectivity -----
echo "--- 2. npm Registry Connectivity ---"
echo ""

echo "Pinging npm registry..."
npm ping 2>&1
echo ""

# ----- SECTION 3: Core Frontend Packages -----
echo "--- 3. Core Frontend Packages (npm view) ---"
echo "Checking if each package is available from the registry..."
echo ""

CORE_PACKAGES=(
  "react"
  "react-dom"
  "react-router-dom"
  "typescript"
  "vite"
  "tailwindcss"
  "zustand"
  "lucide-react"
  "@radix-ui/react-slot"
  "class-variance-authority"
  "clsx"
  "tailwind-merge"
)

for pkg in "${CORE_PACKAGES[@]}"; do
  version=$(npm view "$pkg" version 2>/dev/null)
  if [ -n "$version" ]; then
    echo "  OK    $pkg  (latest: $version)"
  else
    echo "  FAIL  $pkg  -- not found or not reachable"
  fi
done

echo ""

# ----- SECTION 4: Dev / Build Dependencies -----
echo "--- 4. Dev / Build Dependencies ---"
echo ""

DEV_PACKAGES=(
  "@vitejs/plugin-react"
  "@types/react"
  "@types/react-dom"
  "autoprefixer"
  "postcss"
  "vitest"
  "@testing-library/react"
  "@testing-library/jest-dom"
  "eslint"
)

for pkg in "${DEV_PACKAGES[@]}"; do
  version=$(npm view "$pkg" version 2>/dev/null)
  if [ -n "$version" ]; then
    echo "  OK    $pkg  (latest: $version)"
  else
    echo "  FAIL  $pkg  -- not found or not reachable"
  fi
done

echo ""

# ----- SECTION 5: Optional / Nice-to-Have -----
echo "--- 5. Optional Packages ---"
echo ""

OPTIONAL_PACKAGES=(
  "prettier"
  "@typescript-eslint/eslint-plugin"
  "@typescript-eslint/parser"
)

for pkg in "${OPTIONAL_PACKAGES[@]}"; do
  version=$(npm view "$pkg" version 2>/dev/null)
  if [ -n "$version" ]; then
    echo "  OK    $pkg  (latest: $version)"
  else
    echo "  FAIL  $pkg  -- not found or not reachable"
  fi
done

echo ""

# ----- SECTION 6: Git -----
echo "--- 6. Git ---"
echo ""

echo "Git version:"
git --version 2>/dev/null || echo "  ERROR: Git is NOT installed"
echo ""

# ----- Summary -----
echo "============================================="
echo "  VERIFICATION COMPLETE"
echo "============================================="
echo ""
echo "Review the output above:"
echo "  OK   = Package is available and installable"
echo "  FAIL = Package was not found -- may be blocked or registry is unreachable"
echo ""
echo "If any FAIL results appear, check with your network/IT team whether"
echo "the npm registry or specific packages are blocked by the corporate proxy."
echo ""
