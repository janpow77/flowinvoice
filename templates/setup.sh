#!/bin/bash
# FlowAudit Template Setup Script
# Usage: ./setup.sh [login|ui-kit|both] [target-directory]

set -e

TEMPLATE=${1:-both}
TARGET=${2:-.}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 FlowAudit Template Setup"
echo "=========================="
echo ""

# Create target if it doesn't exist
mkdir -p "$TARGET"

case $TEMPLATE in
  login)
    echo "📦 Installing Login Template..."
    cp -r "$SCRIPT_DIR/login-template/"* "$TARGET/"
    echo "✅ Login template installed!"
    ;;

  ui-kit)
    echo "📦 Installing UI Kit Template..."
    cp -r "$SCRIPT_DIR/ui-kit-template/"* "$TARGET/"
    echo "✅ UI Kit template installed!"
    ;;

  both)
    echo "📦 Installing both templates..."

    # UI Kit first (base)
    mkdir -p "$TARGET/frontend/src"
    cp -r "$SCRIPT_DIR/ui-kit-template/frontend/src/styles" "$TARGET/frontend/src/"
    cp -r "$SCRIPT_DIR/ui-kit-template/frontend/src/components" "$TARGET/frontend/src/"
    cp -r "$SCRIPT_DIR/ui-kit-template/frontend/src/context/ThemeContext.tsx" "$TARGET/frontend/src/context/"
    cp "$SCRIPT_DIR/ui-kit-template/frontend/tailwind.config.js" "$TARGET/frontend/"
    cp -r "$SCRIPT_DIR/ui-kit-template/frontend/public" "$TARGET/frontend/"

    # Login template (adds auth)
    cp -r "$SCRIPT_DIR/login-template/frontend/pages" "$TARGET/frontend/src/"
    cp "$SCRIPT_DIR/login-template/frontend/context/AuthContext.tsx" "$TARGET/frontend/src/context/"
    cp -r "$SCRIPT_DIR/login-template/backend" "$TARGET/"

    echo "✅ Both templates installed!"
    ;;

  *)
    echo "❌ Unknown template: $TEMPLATE"
    echo "Usage: ./setup.sh [login|ui-kit|both] [target-directory]"
    exit 1
    ;;
esac

echo ""
echo "📁 Files installed to: $TARGET"
echo ""
echo "Next steps:"
echo "  1. cd $TARGET"
echo "  2. npm install tailwindcss clsx lucide-react react-router-dom axios"
echo "  3. Update paths in components to match your structure"
echo "  4. Replace logo files in public/"
echo ""
echo "Done! 🎉"
