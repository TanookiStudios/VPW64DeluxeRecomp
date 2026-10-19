// The launcher page, in the house style shared by the other Tanooki Studios ports: a header with
// the port's own icon, title and platform line, Game / Settings / About buttons at the top right,
// a ROM panel and a player panel, PLAY at the bottom right, and an About page with Maddie's
// letter, her signature and a Leave a Tip button. Built from the frontend's element classes.
#include <string>
#include <vector>
#include <filesystem>

#include <SDL.h>

#include "librecomp/game.hpp"
#include "recompinput/players.h"
#include "recompui/recompui.h"
#include "recompui/config.h"
#include "util/file.h"
#include "base/ui_launcher.h"
#include "elements/ui_button.h"
#include "elements/ui_container.h"
#include "elements/ui_image.h"
#include "elements/ui_label.h"
#include "elements/ui_svg.h"

#include "icon_bytes.h"
#include "signature_bytes.h"

using namespace recompui;

namespace {
    const std::string game_tab_id = "game";
    const Color panel_bg{13, 19, 38, 255};
    const Color panel_border{32, 44, 74, 255};
    const Color header_line{47, 128, 255, 255};
    const Color accent{47, 128, 255, 255};
    const Color dim{139, 149, 176, 255};
    const Color good{61, 220, 132, 255};
    const Color warn{255, 196, 64, 255};

    const char* about_paragraphs[] = {
        "Hi, I'm Maddie. I make apps and games on my own at Tanooki Studios.",
        "Virtual Pro Wrestling 2 is the wrestling game I kept hearing was the best one on the Nintendo 64, "
        "and the Deluxe fan edition by Lowwater adds even more to it. I wanted it to run on a modern computer "
        "the way it should: sharp, with controllers that just work, and a few cheats for when the ref is slow.",
        "It's free, and it'll stay free. You bring your own copy of the game; nothing from the original cartridge "
        "ships with this. It isn't made by or affiliated with AKI, Asmik Ace, Lowwater or Nintendo.",
        "Making apps (including some decomps) is how I pay my bills. If this game brought you some nostalgia "
        "and you ever got pinned at 29:59 of a thirty-minute match, feel free to drop me a tiny tip. "
        "It really helps!",
    };

    struct LauncherState {
        std::u8string game_id;
        Element* home = nullptr;
        Element* about = nullptr;
        Element* top_buttons = nullptr;
        Button* back_button = nullptr;
        Label* rom_status = nullptr;
        Label* rom_file = nullptr;
        Button* play = nullptr;
        Button* browse = nullptr;
        Button* nav_game = nullptr; Button* nav_settings = nullptr; Button* nav_about = nullptr;
    } st;

    Element* panel(ContextId ctx, Element* parent) {
        Element* p = ctx.create_element<Element>(parent, 0, "div", false);
        p->set_display(Display::Flex);
        p->set_flex_direction(FlexDirection::Column);
        p->set_background_color(panel_bg);
        p->set_border_width(1.0f);
        p->set_border_color(panel_border);
        p->set_border_radius(10.0f);
        p->set_padding(24.0f);
        p->set_gap(10.0f);
        return p;
    }

    // "| SECTION" heading: a short accent bar and spaced small caps, like the other launchers.
    void section(ContextId ctx, Element* parent, const std::string& text) {
        Element* row = ctx.create_element<Element>(parent, 0, "div", false);
        row->set_display(Display::Flex);
        row->set_flex_direction(FlexDirection::Row);
        row->set_align_items(AlignItems::Center);
        row->set_gap(8.0f);
        row->set_margin_bottom(6.0f);
        Element* bar = ctx.create_element<Element>(row, 0, "div", false);
        bar->set_width(3.0f); bar->set_height(16.0f); bar->set_background_color(accent);
        Label* l = ctx.create_element<Label>(row, text, theme::Typography::LabelSM);
        l->set_color(accent); l->set_letter_spacing(2.0f); l->set_text_transform(TextTransform::Uppercase);
    }

    void refresh_rom_state() {
        bool valid = recomp::is_rom_valid(st.game_id);
        if (valid) {
            st.rom_status->set_text("ROM verified");
            st.rom_status->set_color(good);
            st.rom_file->set_text("Your Virtual Pro Wrestling 64 Deluxe ROM is stored and checked. Press PLAY.");
            st.play->set_text("PLAY");
        } else {
            st.rom_status->set_text("No ROM yet");
            st.rom_status->set_color(warn);
            st.rom_file->set_text("Press Browse and pick your own Virtual Pro Wrestling 64 Deluxe .z64 file.");
            st.play->set_text("LOAD ROM");
        }
    }

    void browse_for_rom() {
        file::open_file_dialog([](bool success, const std::filesystem::path& path) {
            if (!success) return;
            auto err = recomp::select_rom(path, st.game_id);
            if (err == recomp::RomValidationError::Good) {
                refresh_rom_state();
            } else {
                open_info_prompt("That file is not the right ROM",
                    "The launcher only accepts the Virtual Pro Wrestling 64 Deluxe cartridge image (a 63.7 MB .z64 file, "
                    "SHA-1 2ad9eb023a93f74c4f77e313a8bd583cec0c53d9). Other versions and other games will not work.",
                    "OK", []() {}, ButtonStyle::Primary);
            }
        });
    }

    void show_about(bool show) {
        st.home->set_display(show ? Display::None : Display::Flex);
        st.about->set_display(show ? Display::Flex : Display::None);
        st.top_buttons->set_display(show ? Display::None : Display::Flex);
        st.back_button->set_display(show ? Display::Flex : Display::None);
    }

    void open_settings_tab(const std::string& tab_id) {
        config::set_tab(tab_id);
        hide_all_contexts();
        config::open();
    }
}

void vpw64dx_build_launcher(LauncherMenu* menu, const std::u8string& game_id, const std::string& mod_game_id) {
    st.game_id = game_id;
    auto ctx = get_current_context();
    menu->remove_default_title();
    update_game_mod_id(mod_game_id);

    static const std::string mark_src = "?/game/tanooki.vpw64deluxe/mark";
    static const std::string sig_src = "?/game/tanooki.vpw64deluxe/signature";
    queue_image_from_bytes_file(mark_src, std::vector<char>(icon_bytes, icon_bytes + icon_bytes_size));
    queue_image_from_bytes_file(sig_src, std::vector<char>(signature_bytes, signature_bytes + signature_bytes_size));

    Element* root = menu->get_menu_container();
    root->set_display(Display::Flex);
    root->set_flex_direction(FlexDirection::Column);
    root->set_gap(16.0f);

    // Header: icon, title and platform on the left; Game / Settings / About on the right.
    Element* header = ctx.create_element<Element>(root, 0, "div", false);
    header->set_display(Display::Flex);
    header->set_flex_direction(FlexDirection::Row);
    header->set_align_items(AlignItems::Center);
    header->set_justify_content(JustifyContent::SpaceBetween);
    header->set_padding_bottom(14.0f);
    header->set_border_bottom_width(2.0f);
    header->set_border_bottom_color(header_line);
    {
        Element* left = ctx.create_element<Element>(header, 0, "div", false);
        left->set_display(Display::Flex); left->set_flex_direction(FlexDirection::Row);
        left->set_align_items(AlignItems::Center); left->set_gap(14.0f);
        Image* mark = ctx.create_element<Image>(left, mark_src);
        mark->set_width(44.0f); mark->set_height(44.0f);
        Element* titles = ctx.create_element<Element>(left, 0, "div", false);
        titles->set_display(Display::Flex); titles->set_flex_direction(FlexDirection::Column); titles->set_gap(2.0f);
        ctx.create_element<Label>(titles, "Virtual Pro Wrestling 64 Deluxe", theme::Typography::Header3);
        Label* platform = ctx.create_element<Label>(titles, "NINTENDO 64", theme::Typography::LabelSM);
        platform->set_color(dim); platform->set_letter_spacing(1.5f);

        st.top_buttons = ctx.create_element<Element>(header, 0, "div", false);
        st.top_buttons->set_display(Display::Flex); st.top_buttons->set_flex_direction(FlexDirection::Row); st.top_buttons->set_gap(10.0f);
        Button* game = ctx.create_element<Button>(st.top_buttons, "Game", ButtonStyle::Secondary, ButtonSize::Medium);
        game->add_pressed_callback([]() { open_settings_tab(game_tab_id); });
        Button* settings = ctx.create_element<Button>(st.top_buttons, "Settings", ButtonStyle::Secondary, ButtonSize::Medium);
        settings->add_pressed_callback([]() { open_settings_tab(config::general::id); });
        Button* about = ctx.create_element<Button>(st.top_buttons, "About", ButtonStyle::Secondary, ButtonSize::Medium);
        about->add_pressed_callback([]() { show_about(true); });

        st.back_button = ctx.create_element<Button>(header, "< Back", ButtonStyle::Secondary, ButtonSize::Medium);
        st.back_button->add_pressed_callback([]() { show_about(false); });
        st.back_button->set_display(Display::None);
        st.back_button->set_min_width(120.0f);
        // Controller navigation: the three header buttons form a row; Down from any of them goes to PLAY.
        game->set_nav(NavDirection::Right, settings); settings->set_nav(NavDirection::Left, game);
        settings->set_nav(NavDirection::Right, about); about->set_nav(NavDirection::Left, settings);
        st.nav_game = game; st.nav_settings = settings; st.nav_about = about;
    }

    // Home: the ROM panel and the player panel side by side.
    st.home = ctx.create_element<Element>(root, 0, "div", false);
    st.home->set_display(Display::Flex); st.home->set_flex_direction(FlexDirection::Row);
    st.home->set_gap(16.0f); st.home->set_flex_grow(1.0f);
    {
        Element* rom = panel(ctx, st.home);
        rom->set_flex(1.0f, 1.0f, 0.0f);
        section(ctx, rom, "Game");
        Element* art = ctx.create_element<Element>(rom, 0, "div", false);
        art->set_display(Display::Flex); art->set_justify_content(JustifyContent::Center); art->set_padding(10.0f);
        Image* big = ctx.create_element<Image>(art, mark_src);
        big->set_width(160.0f); big->set_height(160.0f);
        st.rom_status = ctx.create_element<Label>(rom, "", theme::Typography::LabelLG);
        st.rom_status->set_text_align(TextAlign::Center);
        st.rom_file = ctx.create_element<Label>(rom, "", theme::Typography::Body);
        st.rom_file->set_color(dim); st.rom_file->set_text_align(TextAlign::Center);
        Element* facts = ctx.create_element<Element>(rom, 0, "div", false);
        facts->set_display(Display::Flex); facts->set_flex_direction(FlexDirection::Column); facts->set_gap(4.0f); facts->set_margin_top(10.0f);
        auto fact = [&](const char* k, const char* v) {
            Element* row = ctx.create_element<Element>(facts, 0, "div", false);
            row->set_display(Display::Flex); row->set_flex_direction(FlexDirection::Row); row->set_gap(12.0f);
            Label* kl = ctx.create_element<Label>(row, k, theme::Typography::Body); kl->set_color(dim); kl->set_width(110.0f);
            ctx.create_element<Label>(row, v, theme::Typography::Body);
        };
        fact("Game", "Virtual Pro Wrestling 64 Deluxe");
        fact("Based on", "Virtual Pro Wrestling 2 (AKI / Asmik Ace, 2000)");
        fact("Mod by", "Lowwater, 2026");
        fact("Region", "Japan (NA2J)");
        fact("Save", "Cartridge SRAM, kept in your settings folder");
        st.browse = ctx.create_element<Button>(rom, "Browse for ROM", ButtonStyle::Secondary, ButtonSize::Medium);
        st.browse->set_margin_top(12.0f);
        st.browse->add_pressed_callback([]() { browse_for_rom(); });

        Element* player = panel(ctx, st.home);
        player->set_flex(1.0f, 1.0f, 0.0f);
        section(ctx, player, "Player 1");
        Label* pl = ctx.create_element<Label>(player, "Keyboard or any controller, no setup. Plug a pad in and it is player 1; the keyboard keeps working alongside it.", theme::Typography::Body);
        pl->set_color(dim);
        ctx.create_element<Label>(player, "Keyboard: W A S D move, Space is A, Left Shift is B, the arrow keys are the C buttons, I J K L are the control stick, E and R are L and R, Q is Z, Enter is Start. Esc (or Back on a controller) opens this port's menu in the game.", theme::Typography::Body);
        Button* configure = ctx.create_element<Button>(player, "Configure controls", ButtonStyle::Secondary, ButtonSize::Medium);
        configure->set_margin_top(12.0f);
        configure->add_pressed_callback([]() { open_settings_tab(config::controls::id); });
        section(ctx, player, "Cheats");
        Label* ch = ctx.create_element<Label>(player, "Unlock all wrestlers, can't be hurt, triple damage, special always ready and weak opponents. Turn them on under Settings, Cheats.", theme::Typography::Body);
        ch->set_color(dim);
    }

    // About: Maddie's letter, signature, tip.
    st.about = ctx.create_element<Element>(root, 0, "div", false);
    st.about->set_display(Display::None); st.about->set_flex_direction(FlexDirection::Column); st.about->set_flex_grow(1.0f);
    {
        Element* p = panel(ctx, st.about);
        section(ctx, p, "About");
        for (const char* para : about_paragraphs) {
            Label* l = ctx.create_element<Label>(p, para, theme::Typography::Body);
            l->set_margin_bottom(6.0f);
        }
        Image* sig = ctx.create_element<Image>(p, sig_src);
        sig->set_width(240.0f); sig->set_height(240.0f * 100.0f / 420.0f);
        sig->set_margin_top(10.0f);
        Button* tip = ctx.create_element<Button>(p, "Leave a Tip", ButtonStyle::Secondary, ButtonSize::Medium);
        tip->set_margin_top(14.0f); tip->set_width(220.0f);
        tip->add_pressed_callback([]() { SDL_OpenURL("https://tanookistudios.com/SupportMe"); });
    }

    // Footer: PLAY at the right.
    Element* footer = ctx.create_element<Element>(root, 0, "div", false);
    footer->set_display(Display::Flex); footer->set_flex_direction(FlexDirection::Row);
    footer->set_justify_content(JustifyContent::FlexEnd);
    footer->set_padding_top(14.0f);
    footer->set_border_top_width(1.0f); footer->set_border_top_color(panel_border);
    st.play = ctx.create_element<Button>(footer, "PLAY", ButtonStyle::Primary, ButtonSize::Large);
    st.play->set_width(220.0f);
    st.play->add_pressed_callback([]() {
        if (recomp::is_rom_valid(st.game_id)) recomp::start_game(st.game_id, {});
        else browse_for_rom();
    });
    st.play->set_nav(NavDirection::Up, st.nav_game);
    for (Button* b : { st.nav_game, st.nav_settings, st.nav_about }) b->set_nav(NavDirection::Down, st.play);
    st.back_button->set_nav(NavDirection::Down, st.play); st.play->set_nav(NavDirection::Left, st.browse);
    st.play->set_as_primary_focus(true);
    ctx.set_autofocus_element(st.play);
    refresh_rom_state();
}
