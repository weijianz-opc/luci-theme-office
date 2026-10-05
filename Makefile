#
# luci-theme-office — isometric "AI Office" glass theme for LuCI
# Licensed to the public under the Apache License 2.0.
#
# Build inside an OpenWrt SDK / buildroot:
#   git clone https://github.com/weijianz-opc/luci-theme-office <sdk>/package/luci-theme-office
#   make package/luci-theme-office/compile V=s
#

include $(TOPDIR)/rules.mk

LUCI_TITLE:=Office theme (isometric glass UI)
LUCI_DEPENDS:=
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0

define Package/luci-theme-office/postrm
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
	uci -q delete luci.themes.Office
	uci -q get luci.main.mediaurlbase | grep -q '/luci-static/office' && \
		uci set luci.main.mediaurlbase='/luci-static/bootstrap'
	uci commit luci
}
endef

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
