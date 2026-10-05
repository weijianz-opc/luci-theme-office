'use strict';
'require baseclass';
'require ui';

/*
 * luci-theme-office menu renderer
 *  - #mainmenu : sidebar "leaderboard" of top-level categories, expandable
 *  - #topmenu  : pill bar with the pages of the active category
 *  - #tabmenu  : page tabs (same as bootstrap)
 *  - #stepbar  : bottom numbered step bar of categories
 */

const COLORS = ['#5df2a0', '#ffc94a', '#7aa2ff', '#a78bfa', '#5ee6ff', '#ff7eb6', '#ff9f5a', '#c6f36b', '#f3a6ff', '#8a8fa8'];

const ICONS = {
	status:     '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
	system:     '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
	services:   '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
	network:    '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M12 7.5v4M12 11.5 6.5 17M12 11.5l5.5 5.5"/>',
	statistics: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
	vpn:        '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
	nas:        '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
	docker:     '<path d="M2 12h18c0 5-4 8-9 8S2 17 2 12zM5 9h3v3H5zM8 9h3v3H8zM11 9h3v3h-3zM8 6h3v3H8z"/>',
	control:    '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
	logout:     '<path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4M10 16l4-4-4-4M14 12H4"/>'
};

function icon(name, idx) {
	const color = COLORS[idx % COLORS.length];
	const span = E('span', { 'class': 'o-ico', 'style': '--c:' + color });

	if (ICONS[name])
		span.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>';
	else
		span.appendChild(E('b', {}, [ (name || '?').charAt(0).toUpperCase() ]));

	return span;
}

return baseclass.extend({
	__init__() {
		ui.menu.load().then((tree) => this.render(tree));
		this.bindSidebar();
	},

	render(tree) {
		let node = tree;
		let url = '';

		this.renderModeMenu(tree);

		if (L.env.dispatchpath.length >= 3) {
			for (let i = 0; i < 3 && node; i++) {
				node = node.children[L.env.dispatchpath[i]];
				url = url + (url ? '/' : '') + L.env.dispatchpath[i];
			}

			if (node)
				this.renderTabMenu(node, url);
		}
	},

	/* ---------------------------------------------------------- mobile drawer */
	bindSidebar() {
		const btn = document.querySelector('#menu-toggle');
		const scrim = document.querySelector('#scrim');
		const toggle = (open) => {
			const isOpen = (open != null) ? open : !document.body.classList.contains('o-menu-open');
			document.body.classList.toggle('o-menu-open', isOpen);
			if (btn) btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
		};

		if (btn) btn.addEventListener('click', () => toggle());
		if (scrim) scrim.addEventListener('click', () => toggle(false));
		document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') toggle(false); });
	},

	/* ---------------------------------------------------------- sidebar */
	renderMainMenu(tree, url) {
		const ul = document.querySelector('#mainmenu');
		const steps = document.querySelector('#stepbar');
		const children = ui.menu.getChildren(tree);
		const activeName = L.env.dispatchpath[1];
		let activeNode = null;

		children.forEach((child, idx) => {
			const subs = ui.menu.getChildren(child);
			const isActive = (child.name === activeName);
			const href = subs.length ? L.url(url, child.name, subs[0].name) : L.url(url, child.name);
			const li = E('li', { 'class': (isActive ? 'active open' : '') });

			const row = E('a', { 'class': 'o-row', 'href': href, 'data-name': child.name }, [
				E('span', { 'class': 'o-idx' }, [ String(idx + 1) ]),
				icon(child.name, idx),
				E('span', { 'class': 'o-name' }, [ _(child.title) ]),
				E('span', { 'class': 'o-val' }, [ subs.length ? String(subs.length) : '' ])
			]);

			if (subs.length) {
				row.addEventListener('click', (ev) => {
					/* first click expands, a click on an expanded entry navigates */
					if (!li.classList.contains('open')) {
						ev.preventDefault();
						ul.querySelectorAll(':scope > li.open').forEach((o) => { if (o !== li && !o.classList.contains('active')) o.classList.remove('open'); });
						li.classList.add('open');
					}
				});

				const sub = E('ul', { 'class': 'o-sub' });
				subs.forEach((s) => {
					const sActive = isActive && L.env.dispatchpath[2] === s.name;
					sub.appendChild(E('li', { 'class': sActive ? 'active' : '' }, [
						E('a', { 'href': L.url(url, child.name, s.name) }, [ _(s.title) ])
					]));
				});

				li.appendChild(row);
				li.appendChild(sub);
			}
			else {
				li.appendChild(row);
			}

			ul.appendChild(li);

			/* bottom step bar */
			if (steps) {
				steps.appendChild(E('li', { 'class': isActive ? 'hot' : '' }, [
					E('a', { 'href': href, 'class': 'o-step' }, [
						E('span', { 'class': 'n', 'style': '--c:' + COLORS[idx % COLORS.length] }, [ String(idx + 1) ]),
						E('span', {}, [ _(child.title) ]),
						subs.length ? E('span', { 'class': 'v' }, [ String(subs.length) ]) : ''
					])
				]));
			}

			if (isActive)
				activeNode = child;
		});

		if (steps && steps.children.length)
			steps.style.display = '';

		if (activeNode)
			this.renderTopMenu(activeNode, url + '/' + activeNode.name);
	},

	/* ---------------------------------------------------------- top pills */
	renderTopMenu(node, url) {
		const ul = document.querySelector('#topmenu');
		const children = ui.menu.getChildren(node);

		children.forEach((child) => {
			const isActive = (L.env.dispatchpath[2] === child.name);
			ul.appendChild(E('li', { 'class': isActive ? 'active' : '' }, [
				E('a', { 'href': L.url(url, child.name) }, [ _(child.title) ])
			]));
		});

		if (ul.children.length) {
			ul.style.display = '';
			const act = ul.querySelector('li.active');
			if (act) ul.scrollLeft = act.offsetLeft - 40;
		}
	},

	/* ---------------------------------------------------------- tabs */
	renderTabMenu(tree, url, level) {
		const container = document.querySelector('#tabmenu');
		const ul = E('ul', { 'class': 'tabs' });
		const children = ui.menu.getChildren(tree);
		let activeNode = null;

		children.forEach((child) => {
			const isActive = (L.env.dispatchpath[3 + (level || 0)] == child.name);
			const className = 'tabmenu-item-%s %s'.format(child.name, isActive ? 'active' : '');

			ul.appendChild(E('li', { 'class': className }, [
				E('a', { 'href': L.url(url, child.name) }, [ _(child.title) ])
			]));

			if (isActive)
				activeNode = child;
		});

		if (ul.children.length == 0)
			return E([]);

		container.appendChild(ul);
		container.style.display = '';

		if (activeNode)
			this.renderTabMenu(activeNode, url + '/' + activeNode.name, (level || 0) + 1);

		return ul;
	},

	/* ---------------------------------------------------------- mode menu */
	renderModeMenu(tree) {
		const ul = document.querySelector('#modemenu');
		const children = ui.menu.getChildren(tree);

		children.forEach((child, index) => {
			const isActive = L.env.requestpath.length ? child.name === L.env.requestpath[0] : index === 0;

			ul.appendChild(E('li', { 'class': isActive ? 'active' : '' }, [
				E('a', { 'href': L.url(child.name) }, [ _(child.title) ])
			]));

			if (isActive)
				this.renderMainMenu(child, child.name);
		});

		if (ul.children.length > 1)
			ul.style.display = '';
	}
});
