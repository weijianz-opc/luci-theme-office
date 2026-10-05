#!/bin/sh
# luci-theme-office installer (no package manager needed)
#
#   install:    wget -qO- https://raw.githubusercontent.com/weijianz-opc/luci-theme-office/main/install.sh | sh
#   uninstall:  wget -qO- https://raw.githubusercontent.com/weijianz-opc/luci-theme-office/main/install.sh | sh -s uninstall
#
# Optional: REF=v1.0.0 to install a tag instead of main.

set -e

REPO="weijianz-opc/luci-theme-office"
REF="${REF:-main}"
UCODE_DIR="/usr/share/ucode/luci/template/themes"

die() { echo "error: $*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "please run as root"

uninstall() {
	if [ "$(uci -q get luci.main.mediaurlbase)" = "/luci-static/office" ]; then
		uci set luci.main.mediaurlbase=/luci-static/bootstrap
	fi
	uci -q delete luci.themes.Office || true
	uci commit luci
	rm -rf /www/luci-static/office "$UCODE_DIR/office" /www/luci-static/resources/menu-office.js
	rm -f /etc/uci-defaults/30_luci-theme-office
	echo "luci-theme-office removed (theme reset to bootstrap)."
}

if [ "$1" = "uninstall" ]; then
	uninstall
	exit 0
fi

[ -d "$UCODE_DIR" ] || die "this theme needs a ucode based LuCI (OpenWrt 23.05 or newer)"

TMP="$(mktemp -d /tmp/luci-theme-office.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

case "$REF" in
	v*) URL="https://github.com/$REPO/archive/refs/tags/$REF.tar.gz" ;;
	*)  URL="https://github.com/$REPO/archive/refs/heads/$REF.tar.gz" ;;
esac

echo "Downloading $URL"
wget -qO "$TMP/src.tar.gz" "$URL" || die "download failed (is ca-certificates / ssl support installed?)"
tar xzf "$TMP/src.tar.gz" -C "$TMP"
SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n1)"
[ -f "$SRC/ucode/template/themes/office/header.ut" ] || die "unexpected archive layout"

mkdir -p /www/luci-static "$UCODE_DIR"
cp -r "$SRC/htdocs/luci-static/." /www/luci-static/
cp -r "$SRC/ucode/template/themes/office" "$UCODE_DIR/"
sh "$SRC/root/etc/uci-defaults/30_luci-theme-office"

rm -f /tmp/luci-indexcache* 2>/dev/null || true
echo "luci-theme-office installed and set as default. Reload LuCI in your browser (Ctrl/Cmd+Shift+R)."
