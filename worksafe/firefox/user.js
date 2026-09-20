// Remainder — Firefox preferences. worksafe/firefox/user.js: copied into the profile by install.sh; Firefox
// reads it at every start and it overrides prefs.js. Implements AUTHORITY.md §0 (the removal, which is the
// larger half), §5 (the two typefaces), and PLATFORM.md Firefox. Delete the file and Firefox forgets it.
//
// Every pref below was checked against the shipped defaults of the build it was written for -- Firefox 155.0.1
// (deb), 2026-09-19 -- by reading defaults/preferences/firefox.js and greprefs.js out of omni.ja. Prefs the
// parent kit carried that no longer exist in 155 are not carried here: extensions.pocket.enabled (Pocket was
// withdrawn), browser.messaging-system.whatsNewPanel.enabled, browser.tabs.firefox-view,
// browser.theme.toolbar-theme and its content-theme pair, browser.promo.focus.enabled. A pref for a feature
// that is gone is not harmless -- it is a line that looks like it is doing something.

// the chrome stylesheets (chrome/userChrome.css, chrome/userContent.css)
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// §2: Firefox draws its own titlebar, so the tab strip can be the ACCENT key titlebar. This is the only
// surface on this desktop that can show key/non-key state at all -- PLATFORM.md records that this libcosmic
// paints header bars with the window background, so every native window reads as non-key.
user_pref("browser.tabs.inTitlebar", 1);
user_pref("browser.uidensity", 1);                                 // compact, as the COSMIC toolkit config
user_pref("browser.compactmode.show", true);
user_pref("widget.gtk.rounded-bottom-corners.enabled", false);     // §5: square, every corner
user_pref("widget.gtk.overlay-scrollbars.enabled", false);         // PLATFORM.md: scrollbars always shown
user_pref("ui.prefersReducedMotion", 1);                           // §0: motion is in the user's way

// §2 is a light palette: WHITE fields, BLACK text. No dark builder is shipped, on this surface or on COSMIC.
user_pref("layout.css.prefers-color-scheme.content-override", 1);
user_pref("ui.systemUsesDarkTheme", 0);
// Firefox 155 added a "use system colours" switch. With it on, the -moz-native-theme media query matches and
// the chrome takes GTK's colours for everything the kit has not named. The user sheet wins either way -- a
// user-origin !important outranks any author-origin rule, layered or not -- but a surface that depends on
// which way a switch is set is not a measured surface.
user_pref("browser.theme.native-theme", false);
// The design system's grey ramp is renumbered under `nova`, and build/firefox.py derives the kit's ramp
// against the numbering in force. Pinning the pref keeps the derivation true. Turn it on and the ladder still
// lands on the kit's four neutrals -- that is what snapping buys -- but three slots move one step, so re-run
// `python3 build/firefox.py --derive` and re-read the sheet before trusting it.
user_pref("browser.nova.enabled", false);

// §5: UI Montserrat, mono Hack. These are the CONTENT defaults; the chrome's own face is set in
// userChrome.css. A page that names its own font keeps it (§0a: content is exempt).
user_pref("font.default.x-western", "sans-serif");
user_pref("font.name.sans-serif.x-western", "Montserrat");
user_pref("font.name.monospace.x-western", "Hack");

// §0: the larger half. Recommendations, sponsorship, nags, promotions, and the machine-learning features
// Firefox 155 turns on by default.
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.highlights", false);
user_pref("browser.newtabpage.activity-stream.showWeather", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
user_pref("browser.topsites.contile.enabled", false);              // sponsored tiles, at their source
user_pref("browser.urlbar.suggest.quicksuggest.sponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.trending", false);
user_pref("browser.urlbar.trending.featureGate", false);
user_pref("browser.urlbar.suggest.recentsearches", false);
user_pref("browser.urlbar.suggest.weather", false);
user_pref("browser.ml.chat.enabled", false);                       // 155: a chatbot in the sidebar, on by default
user_pref("browser.tabs.groups.smart.enabled", false);             // 155: machine-suggested tab groups
user_pref("browser.tabs.groups.smart.userEnabled", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");   // no "what's new" page after an update
user_pref("browser.vpn_promo.enabled", false);
user_pref("browser.promo.pin.enabled", false);
user_pref("browser.contentblocking.report.hide_vpn_banner", true);
user_pref("browser.preferences.moreFromMozilla", false);           // a promotion pane inside Settings
user_pref("browser.tabs.hoverPreview.enabled", false);             // §0: motion, and a thing that appears
user_pref("browser.discovery.enabled", false);
user_pref("extensions.getAddons.showPane", false);
user_pref("extensions.htmlaboutaddons.recommendations.enabled", false);
