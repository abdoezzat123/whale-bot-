#!/usr/bin/env bash
# ============================================
# 🚀 سكريبت تشغيل بوت الحيتان بأمر واحد
# ============================================
# يدعم: AWS EC2 / Oracle Cloud / Google Cloud / أي VPS Ubuntu/Debian
#
# الاستخدام:
#   ./deploy.sh              # تشغيل
#   ./deploy.sh logs         # شوف الـ logs
#   ./deploy.sh restart      # ريستارت
#   ./deploy.sh stop         # وقف
#   ./deploy.sh status       # حالة
#   ./deploy.sh update       # تحديث من GitHub
#   ./deploy.sh uninstall    # حذف كامل

set -e

# ألوان للطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()  { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_ok()    { echo -e "${GREEN}✅ $1${NC}"; }
print_warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_err()   { echo -e "${RED}❌ $1${NC}"; }

# إعدادات
BOT_DIR="${BOT_DIR:-$HOME/whale-bot}"
COMPOSE_FILE="$BOT_DIR/docker-compose.yml"

# تحقق إن الكود بيتشغل من الـ bot dir
if [[ ! -f "$BOT_DIR/bot.py" ]]; then
    print_err "ملف bot.py مش موجود في $BOT_DIR"
    print_info "نزّل المشروع الأول:"
    echo "  git clone https://github.com/USERNAME/whale-bot.git $BOT_DIR"
    exit 1
fi

cd "$BOT_DIR"

# ===== Helper functions =====
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_err "Docker مش متثبت"
        print_info "تثبيت Docker..."
        curl -fsSL https://get.docker.com | sudo sh
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker $USER
        print_warn "اعمل logout و login تاني علشان الـ docker group يتفعل"
        exit 0
    fi
    print_ok "Docker موجود: $(docker --version)"
}

check_env() {
    if [[ ! -f ".env" ]]; then
        print_err "ملف .env مش موجود!"
        print_info "انسخ .env.example لـ .env واملأ القيم:"
        echo "  cp .env.example .env"
        echo "  nano .env"
        exit 1
    fi

    # تحقق إن التوكن موجود
    if grep -q "ضع_التوكن\|ضع_الـ\|TELEGRAM_BOT_TOKEN=$" .env; then
        print_err "ملف .env مش مظبوط - في قيم ناقصة"
        print_info "افتح .env واملأ القيم"
        exit 1
    fi
    print_ok "ملف .env مظبوط"
}

# ===== Commands =====
cmd_install() {
    print_info "🚀 بدء تثبيت البوت..."
    check_docker
    check_env

    print_info "📦 عمل build للـ Docker image..."
    docker compose build

    print_info "🎯 تشغيل البوت..."
    docker compose up -d

    print_ok "🎉 البوت اشتغل!"
    echo ""
    print_info "شوف الـ logs:"
    echo "  ./deploy.sh logs"
    echo ""
    print_info "أو مباشرة:"
    echo "  docker compose logs -f"
}

cmd_logs() {
    print_info "📋 عرض الـ logs (Ctrl+C للخروج)..."
    docker compose logs -f --tail=100
}

cmd_restart() {
    print_info "🔄 ريستارت البوت..."
    docker compose restart
    print_ok "تم الريستارت"
}

cmd_stop() {
    print_info "⏹️  وقف البوت..."
    docker compose down
    print_ok "البوت اتوقف"
}

cmd_status() {
    print_info "📊 حالة البوت:"
    docker compose ps
    echo ""
    print_info "📊 إحصائيات الـ container:"
    docker stats --no-stream $(docker compose ps -q) 2>/dev/null || true
}

cmd_update() {
    print_info "⬇️  تحديث من GitHub..."
    git pull
    print_info "🔄 عمل build من جديد..."
    docker compose up -d --build
    print_ok "تم التحديث"
}

cmd_uninstall() {
    print_warn "هتتمسح كل البيانات (الـ database + الـ logs)"
    read -p "هل أنت متأكد؟ (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        docker compose down -v
        rm -rf data/
        print_ok "تم الحذف"
    else
        print_info "اتلغى الحذف"
    fi
}

cmd_help() {
    echo "🚀 بوت تتبع الحيتان - سكريبت التحكم"
    echo ""
    echo "الاستخدام: ./deploy.sh [command]"
    echo ""
    echo "الأوامر:"
    echo "  (فاضي)     تثبيت وتشغيل البوت"
    echo "  logs       عرض الـ logs live"
    echo "  restart    ريستارت البوت"
    echo "  stop       وقف البوت"
    echo "  start      تشغيل البوت (لو متوقف)"
    echo "  status     حالة البوت"
    echo "  update     تحديث من GitHub"
    echo "  uninstall  حذف كامل (مع البيانات)"
    echo "  help       هذه الرسالة"
}

cmd_start() {
    print_info "▶️  تشغيل البوت..."
    docker compose up -d
    print_ok "البوت اشتغل"
}

# ===== Main =====
case "${1:-install}" in
    install|"")  cmd_install ;;
    logs)        cmd_logs ;;
    restart)     cmd_restart ;;
    stop)        cmd_stop ;;
    start)       cmd_start ;;
    status)      cmd_status ;;
    update)      cmd_update ;;
    uninstall)   cmd_uninstall ;;
    help|-h|--help) cmd_help ;;
    *)           print_err "أمر غير معروف: $1"; cmd_help; exit 1 ;;
esac
