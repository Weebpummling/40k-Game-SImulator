import streamlit as st
import random
import copy
import uuid
import pandas as pd
import io

# --- Constants and Configuration ---

BASE_MASTER_CARD_LIST = [
    "Assassination", "Containment", "Behind Enemy Lines", "Marked for Death", 
    "Bring It Down", "No Prisoners", "Defend Stronghold", "Storm Hostile Objective", 
    "Sabotage", "Cull the Horde", "Overwhelming Force", "Extend Battle Lines", 
    "Recover Assets", "Engage on All Fronts", "Area Denial", 
    "Secure No Man's Land", "Cleanse"
]

CARDS_DATA = {
    "Assassination": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Score 5VP", "vp": 5}]
    },
    "Containment": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 3VP", "vp": 3}, {"label": "Additional 3VP", "vp": 3}]
    },
    "Behind Enemy Lines": { 
        "first_turn_restricted": True, 
        "vp_components": [{"label": "Base 3VP", "vp": 3}, {"label": "Additional 1VP", "vp": 1}]
    },
    "Marked for Death": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Score 5VP", "vp": 5}]
    },
    "Bring It Down": { 
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 2VP", "vp": 2}]
    },
    "No Prisoners": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 2VP (A)", "vp": 2}, {"label": "Additional 1VP (B)", "vp": 1}]
    },
    "Defend Stronghold": { 
        "first_turn_restricted": True, 
        "vp_components": [{"label": "Score 3VP", "vp": 3}]
    },
    "Storm Hostile Objective": { 
        "first_turn_restricted": True, 
        "vp_components": [{"label": "Score 4VP", "vp": 4}]
    },
    "Sabotage": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 3VP", "vp": 3}, {"label": "Additional 3VP", "vp": 3}]
    },
    "Cull the Horde": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Score 5VP", "vp": 5}]
    },
    "Overwhelming Force": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 3VP", "vp": 3}, {"label": "Additional 2VP", "vp": 2}]
    },
    "Extend Battle Lines": { 
        "first_turn_restricted": False,
        "vp_components": [{"label": "Score 5VP", "vp": 5}]
    },
    "Recover Assets": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 3VP", "vp": 3}, {"label": "Additional 3VP", "vp": 3}]
    },
    "Engage on All Fronts": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 2VP", "vp": 2}]
    },
    "Area Denial": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 3VP", "vp": 3}]
    },
    "Secure No Man's Land": { 
        "first_turn_restricted": False, 
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 3VP", "vp": 3}]
    },
    "Cleanse": {
        "first_turn_restricted": False,
        "vp_components": [{"label": "Base 2VP", "vp": 2}, {"label": "Additional 2VP", "vp": 2}]
    }
}

MAX_GAME_TURNS = 5
VP_PER_SECONDARY_CARD_INPUT_MAX = 15 
MAX_PRIMARY_VP_PER_TURN_INPUT = 25 
MAX_TOTAL_PRIMARY_VP = 50 
MAX_TOTAL_SECONDARY_VP = 40 
PAINT_BONUS_VP = 10

ROUND_BASED_DEFAULT_PROBABILITIES = {
    "user": { 
        "Assassination": {
            "Score 5VP":         {1: 0.20, 2: 0.30, 3: 0.50, 4: 0.70, 5: 0.80}
        },
        "Containment": {
            "Base 3VP":          {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
            "Additional 3VP":    {1: 1.00, 2: 1.00, 3: 0.80, 4: 0.50, 5: 0.50}
        },
        "Behind Enemy Lines": {
            "Base 3VP":          {1: 0.00, 2: 0.10, 3: 0.30, 4: 0.50, 5: 0.80},
            "Additional 1VP":    {1: 0.00, 2: 0.00, 3: 0.30, 4: 0.50, 5: 0.80}
        },
        "Marked for Death": {
            "Score 5VP":         {1: 0.00, 2: 0.00, 3: 0.20, 4: 0.30, 5: 0.50}
        },
        "Bring It Down": {
            "Base 2VP":          {1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.80},
            "Additional 2VP":    {1: 0.00, 2: 0.30, 3: 0.50, 4: 0.50, 5: 0.50}
        },
        "No Prisoners": {
            "Base 2VP":          {1: 0.20, 2: 0.80, 3: 1.00, 4: 1.00, 5: 1.00},
            "Additional 2VP (A)":{1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.80},
            "Additional 1VP (B)":{1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.80}
        },
        "Defend Stronghold": {
            "Score 3VP":         {1: 0.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00} 
        },
        "Storm Hostile Objective": {
            "Score 4VP":         {1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.50} 
        },
        "Sabotage": {
            "Base 3VP":          {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.50, 5: 0.50},
            "Additional 3VP":    {1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.10}
        },
        "Cull the Horde": {
            "Score 5VP":         {1: 0.00, 2: 0.00, 3: 0.00, 4: 0.10, 5: 0.30}
        },
        "Overwhelming Force": {
            "Base 3VP":          {1: 0.10, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80},
            "Additional 2VP":    {1: 0.00, 2: 0.30, 3: 0.80, 4: 0.80, 5: 0.80}
        },
        "Extend Battle Lines": {
            "Score 5VP":         {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00}
        },
        "Recover Assets": {
            "Base 3VP":          {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.50, 5: 0.50},
            "Additional 3VP":    {1: 0.00, 2: 0.00, 3: 0.30, 4: 0.30, 5: 0.30}
        },
        "Engage on All Fronts": {
            "Base 2VP":          {1: 0.80, 2: 0.30, 3: 0.50, 4: 0.80, 5: 0.80},
            "Additional 2VP":    {1: 0.00, 2: 0.30, 3: 0.30, 4: 0.50, 5: 0.50} 
        },
        "Area Denial": {
            "Base 2VP":          {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80},
            "Additional 3VP":    {1: 0.80, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80}
        },
        "Secure No Man's Land": {
            "Base 2VP":          {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
            "Additional 3VP":    {1: 0.80, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80}
        },
        "Cleanse": {
            "Base 2VP":          {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
            "Additional 2VP":    {1: 0.80, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80}
        }
    }
}
ROUND_BASED_DEFAULT_PROBABILITIES["opponent"] = copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES["user"])

# --- Helper Functions ---

def _build_player_active_deck(removal_option_key):
    temp_deck = list(BASE_MASTER_CARD_LIST) 
    removal_choice = st.session_state.get(removal_option_key, 'Keep Both')
    if removal_choice == "Remove Cull the Horde":
        if "Cull the Horde" in temp_deck: temp_deck.remove("Cull the Horde")
    elif removal_choice == "Remove Bring It Down":
        if "Bring It Down" in temp_deck: temp_deck.remove("Bring It Down")
    return temp_deck


def initialize_session_state():
    if 'game_started' not in st.session_state: st.session_state.game_started = False
    if 'user_goes_first' not in st.session_state: st.session_state.user_goes_first = True
    if 'paint_vp_bonus_selected' not in st.session_state: st.session_state.paint_vp_bonus_selected = False
    if 'current_game_turn' not in st.session_state: st.session_state.current_game_turn = 1
    if 'active_player_type' not in st.session_state: st.session_state.active_player_type = "user"
    if 'game_log' not in st.session_state: st.session_state.game_log = []
    
    if 'user_removed_card_option' not in st.session_state: 
        st.session_state.user_removed_card_option = "Keep Both" 
    if 'opponent_removed_card_option' not in st.session_state:
        st.session_state.opponent_removed_card_option = "Keep Both"

    st.session_state.user_active_deck = _build_player_active_deck('user_removed_card_option')
    st.session_state.opponent_active_deck = _build_player_active_deck('opponent_removed_card_option')
    
    if 'mulliganed_cards_by_player' not in st.session_state:
        st.session_state.mulliganed_cards_by_player = {"user": set(), "opponent": set()}
        
    if 'probabilities' not in st.session_state:
        st.session_state.probabilities = {"user": {}, "opponent": {}}
    
    for player_type_init, active_deck_init in [("user", st.session_state.user_active_deck), 
                                               ("opponent", st.session_state.opponent_active_deck)]:
        if player_type_init not in st.session_state.probabilities:
            st.session_state.probabilities[player_type_init] = {}
        
        player_probs = st.session_state.probabilities[player_type_init]
        
        for card_name_init in active_deck_init:
            default_card_prob_components = ROUND_BASED_DEFAULT_PROBABILITIES["user"].get(card_name_init, {})
            
            if card_name_init not in player_probs: 
                player_probs[card_name_init] = copy.deepcopy(default_card_prob_components)
            else: 
                if card_name_init in CARDS_DATA: 
                    for component in CARDS_DATA[card_name_init].get("vp_components", []):
                        comp_label = component["label"]
                        if comp_label not in player_probs[card_name_init]: 
                            player_probs[card_name_init][comp_label] = \
                                copy.deepcopy(default_card_prob_components.get(comp_label, {r: 0.6 for r in range(1, MAX_GAME_TURNS + 1)}))
                        else: 
                            for r_idx_init in range(1, MAX_GAME_TURNS + 1):
                                if r_idx_init not in player_probs[card_name_init][comp_label]:
                                    player_probs[card_name_init][comp_label][r_idx_init] = \
                                        default_card_prob_components.get(comp_label, {}).get(r_idx_init, 0.6)
        
        keys_to_remove_prob = [k for k in player_probs if k not in active_deck_init]
        for k_rem_prob in keys_to_remove_prob:
            del player_probs[k_rem_prob]

    if 'all_primary_vps' not in st.session_state:
        st.session_state.all_primary_vps = {"user": [0] * MAX_GAME_TURNS, "opponent": [0] * MAX_GAME_TURNS}
    if 'current_player_drawn_cards' not in st.session_state: st.session_state.current_player_drawn_cards = []
    if 'current_player_final_hand' not in st.session_state: st.session_state.current_player_final_hand = []
    if 'current_player_card_vps' not in st.session_state: st.session_state.current_player_card_vps = {} 
    if 'turn_segment_in_progress' not in st.session_state: st.session_state.turn_segment_in_progress = False
    if 'current_turn_component_prob_overrides' not in st.session_state:
        st.session_state.current_turn_component_prob_overrides = {}
    if 'monte_carlo_projection' not in st.session_state: 
        st.session_state.monte_carlo_projection = None 
    if 'num_mc_simulations' not in st.session_state: 
        st.session_state.num_mc_simulations = 5000 
    if 'show_confirm_new_game_setup' not in st.session_state:
        st.session_state.show_confirm_new_game_setup = False
    if 'show_confirm_new_game_sidebar' not in st.session_state:
        st.session_state.show_confirm_new_game_sidebar = False


def get_cards_logged_by_player(player_type):
    logged_by_player = set()
    for log_entry in st.session_state.game_log:
        if log_entry['player_type'] == player_type:
            if "final_hand_after_mulligan_or_selection" in log_entry:
                for card_used in log_entry["final_hand_after_mulligan_or_selection"]:
                    if card_used: 
                        logged_by_player.add(card_used)
            elif log_entry.get("card_1_name"): logged_by_player.add(log_entry["card_1_name"])
            elif log_entry.get("card_2_name"): logged_by_player.add(log_entry["card_2_name"])
    return logged_by_player


def get_available_deck(player_type):
    cards_used_by_this_player = get_cards_logged_by_player(player_type)
    mulliganed_out_for_player = st.session_state.mulliganed_cards_by_player.get(player_type, set())
    
    active_deck_for_player = []
    if player_type == "user":
        active_deck_for_player = st.session_state.user_active_deck
    elif player_type == "opponent":
        active_deck_for_player = st.session_state.opponent_active_deck
    
    return [card for card in active_deck_for_player 
            if card not in cards_used_by_this_player and card not in mulliganed_out_for_player]

def calculate_hand_ev(hand, player_type, game_turn, use_overrides=False):
    if not hand: return 0
    total_ev_for_hand = 0
    player_probabilities = st.session_state.probabilities[player_type]
    overrides = st.session_state.get('current_turn_component_prob_overrides', {}) if use_overrides else {}

    for card_name_ev in hand:
        if card_name_ev in CARDS_DATA and card_name_ev in player_probabilities:
            card_specific_ev = 0
            if "vp_components" in CARDS_DATA[card_name_ev]:
                for component in CARDS_DATA[card_name_ev]["vp_components"]:
                    comp_label = component["label"]
                    comp_vp = component["vp"]
                    prob_of_comp = 0.0
                    if player_type == "user" and use_overrides and \
                       card_name_ev in overrides and comp_label in overrides.get(card_name_ev, {}): 
                        prob_of_comp = overrides[card_name_ev][comp_label]
                    elif card_name_ev in player_probabilities and comp_label in player_probabilities.get(card_name_ev, {}): 
                         prob_of_comp = player_probabilities[card_name_ev][comp_label].get(game_turn, 0.0)
                    card_specific_ev += prob_of_comp * comp_vp
            total_ev_for_hand += card_specific_ev
    return total_ev_for_hand


def get_ev_recommendation(ev_score):
    if ev_score < 3.0: return "Low EV. Consider discarding and redrawing heavily."
    elif ev_score < 5.0: return "Moderate EV. Discarding and redrawing might be beneficial."
    else: return "Good EV. Keeping these cards is likely a solid choice."

def start_new_game():
    st.session_state.game_started = True
    st.session_state.user_goes_first = st.session_state.setup_user_goes_first 
    st.session_state.paint_vp_bonus_selected = st.session_state.setup_paint_vp_bonus 
    st.session_state.user_removed_card_option = st.session_state.setup_user_removed_card_option
    st.session_state.opponent_removed_card_option = st.session_state.setup_opponent_removed_card_option
    
    st.session_state.mulliganed_cards_by_player = {"user": set(), "opponent": set()}
    
    if st.session_state.get('setup_reset_probs_on_new_game', True): 
        st.session_state.probabilities = {"user": {}, "opponent": {}} 

    initialize_session_state() 

    st.session_state.current_game_turn = 1 
    st.session_state.active_player_type = "user" if st.session_state.user_goes_first else "opponent" 
    st.session_state.game_log = [] 
    st.session_state.all_primary_vps = {"user": [0]*MAX_GAME_TURNS, "opponent": [0]*MAX_GAME_TURNS} 
    st.session_state.monte_carlo_projection = None 
    
    reset_transient_turn_state() 
    st.session_state.turn_segment_in_progress = False


def reset_transient_turn_state():
    st.session_state.current_player_drawn_cards = []
    st.session_state.current_player_final_hand = []
    st.session_state.current_player_card_vps = {} 
    st.session_state.current_turn_component_prob_overrides = {} 

def draw_initial_cards_for_player(player_type_draw, num_cards_to_draw=2):
    st.session_state.current_turn_component_prob_overrides = {} 
    current_available_deck = get_available_deck(player_type_draw) 
    drawn_cards_list = []
    drew_restricted_in_t1_fallback = False 

    if st.session_state.current_game_turn == 1: 
        eligible_deck_t1 = [card for card in current_available_deck if not CARDS_DATA[card].get("first_turn_restricted", False)]
        if len(eligible_deck_t1) < num_cards_to_draw:
            st.warning(f"T1: Not enough non-restricted cards ({len(eligible_deck_t1)} available for {player_type_draw}). Drawing what's possible.")
            drawn_cards_list = random.sample(eligible_deck_t1, len(eligible_deck_t1)) if eligible_deck_t1 else []
            if len(drawn_cards_list) < num_cards_to_draw: 
                num_still_needed = num_cards_to_draw - len(drawn_cards_list)
                restricted_available_t1 = [card for card in current_available_deck if CARDS_DATA[card].get("first_turn_restricted", False) and card not in drawn_cards_list]
                num_restricted_to_draw = min(num_still_needed, len(restricted_available_t1))
                if num_restricted_to_draw > 0:
                    drawn_cards_list.extend(random.sample(restricted_available_t1, num_restricted_to_draw))
                    drew_restricted_in_t1_fallback = True 
        else: 
            drawn_cards_list = random.sample(eligible_deck_t1, num_cards_to_draw)
    else: 
        actual_num_to_draw = min(num_cards_to_draw, len(current_available_deck)) 
        if actual_num_to_draw < num_cards_to_draw: st.warning(f"Deck low for {player_type_draw}. Drawing {actual_num_to_draw} card(s) instead of {num_cards_to_draw}.")
        if actual_num_to_draw > 0: drawn_cards_list = random.sample(current_available_deck, actual_num_to_draw)
    
    if drew_restricted_in_t1_fallback: 
        st.warning("T1 Draw: Due to deck composition, restricted card(s) were drawn.")

    st.session_state.current_player_drawn_cards = drawn_cards_list
    st.session_state.current_player_final_hand = list(drawn_cards_list) 
    st.session_state.turn_segment_in_progress = True 

def manually_select_cards_for_player(player_type_select, selected_cards_manual, max_cards=3): 
    st.session_state.current_turn_component_prob_overrides = {} 
    if st.session_state.current_game_turn == 1: 
        for card_sel in selected_cards_manual:
            if CARDS_DATA[card_sel].get("first_turn_restricted", False):
                st.error(f"Cannot select '{card_sel}' in Turn 1 (it is restricted). Please choose other cards.")
                return False 
    if not (0 <= len(selected_cards_manual) <= max_cards): 
        st.warning(f"Please select between 0 and {max_cards} cards.")
        return False

    st.session_state.current_player_drawn_cards = list(selected_cards_manual)
    st.session_state.current_player_final_hand = list(selected_cards_manual)
    st.session_state.turn_segment_in_progress = True
    return True 

def mulligan_cards(player_type_mulligan, cards_to_mulligan_list): 
    st.session_state.current_turn_component_prob_overrides = {} 
    current_hand_mulligan = st.session_state.current_player_final_hand
    
    for card_mulligan in cards_to_mulligan_list: 
        if card_mulligan in current_hand_mulligan: 
            current_hand_mulligan.remove(card_mulligan)
            st.session_state.mulliganed_cards_by_player[player_type_mulligan].add(card_mulligan)
            st.info(f"{player_type_mulligan.capitalize()} mulliganed '{card_mulligan}'. It is removed from their deck for this game.")


    num_to_redraw_mulligan = len(cards_to_mulligan_list)
    if num_to_redraw_mulligan > 0:
        deck_for_redraw_pool = get_available_deck(player_type_mulligan)
        pool_to_draw_from_mulligan_candidates = [c for c in deck_for_redraw_pool if c not in current_hand_mulligan]
        
        pool_to_draw_from_mulligan = []
        if st.session_state.current_game_turn == 1: 
            t1_mulligan_pool = [c for c in pool_to_draw_from_mulligan_candidates if not CARDS_DATA[c].get("first_turn_restricted", False)]
            if len(t1_mulligan_pool) < num_to_redraw_mulligan:
                st.warning("T1 Mulligan: Limited non-restricted cards for redraw. Drawing from all available valid candidates.")
                pool_to_draw_from_mulligan = pool_to_draw_from_mulligan_candidates
            else:
                pool_to_draw_from_mulligan = t1_mulligan_pool
        else: 
            pool_to_draw_from_mulligan = pool_to_draw_from_mulligan_candidates
        
        actual_redraw_count = min(num_to_redraw_mulligan, len(pool_to_draw_from_mulligan))
        if actual_redraw_count < num_to_redraw_mulligan : st.warning(f"Mulligan: Not enough cards for full redraw. Drawing {actual_redraw_count}.")
        if actual_redraw_count > 0 : current_hand_mulligan.extend(random.sample(pool_to_draw_from_mulligan, actual_redraw_count))
    st.session_state.current_player_final_hand = current_hand_mulligan 

def log_player_turn():
    log_entry_id = str(uuid.uuid4()) 
    active_player = st.session_state.active_player_type
    final_hand_log = st.session_state.current_player_final_hand
    current_game_turn_idx = st.session_state.current_game_turn - 1 
    primary_vp_for_log = st.session_state.all_primary_vps[active_player][current_game_turn_idx]
    
    card_data_for_log = []
    for i in range(min(len(final_hand_log), 3)): 
        card_name = final_hand_log[i]
        card_vp = st.session_state.current_player_card_vps.get(card_name, 0)
        card_data_for_log.append({"name": card_name, "vp": card_vp, "returned": False}) 

    new_log_entry = {
        "log_id": log_entry_id, "game_turn": st.session_state.current_game_turn, "player_type": active_player,
        "primary_vp_logged_for_turn": primary_vp_for_log, 
        "card_1_name": card_data_for_log[0]["name"] if len(card_data_for_log) > 0 else None,
        "card_1_vp": card_data_for_log[0]["vp"] if len(card_data_for_log) > 0 else 0,
        "card_1_returned_to_deck": False,
        "card_2_name": card_data_for_log[1]["name"] if len(card_data_for_log) > 1 else None,
        "card_2_vp": card_data_for_log[1]["vp"] if len(card_data_for_log) > 1 else 0,
        "card_2_returned_to_deck": False,
        "card_3_name": card_data_for_log[2]["name"] if len(card_data_for_log) > 2 else None,
        "card_3_vp": card_data_for_log[2]["vp"] if len(card_data_for_log) > 2 else 0,
        "card_3_returned_to_deck": False,
        "initial_draw": list(st.session_state.current_player_drawn_cards), 
        "final_hand_after_mulligan_or_selection": list(final_hand_log) 
    }
    st.session_state.game_log.append(new_log_entry)

    user_is_first_player = st.session_state.user_goes_first
    if (user_is_first_player and active_player == "opponent") or \
       (not user_is_first_player and active_player == "user"):
        st.session_state.current_game_turn += 1 
        st.session_state.active_player_type = "user" if user_is_first_player else "opponent"
    else: 
        st.session_state.active_player_type = "opponent" if active_player == "user" else "user"
        
    reset_transient_turn_state() 
    st.session_state.turn_segment_in_progress = False 

def calculate_total_scores():
    scores_dict = {ptype: {"raw_primary": 0, "raw_secondary": 0, "capped_primary": 0, 
                           "capped_secondary": 0, "paint_vp": 0, "total": 0} 
                   for ptype in ["user", "opponent"]}

    for player_key in ["user", "opponent"]:
        scores_dict[player_key]["raw_primary"] = sum(st.session_state.all_primary_vps[player_key])
        scores_dict[player_key]["capped_primary"] = min(scores_dict[player_key]["raw_primary"], MAX_TOTAL_PRIMARY_VP)
        current_raw_secondary = 0
        for entry_log in st.session_state.game_log:
            if entry_log["player_type"] == player_key:
                if entry_log["card_1_name"]: current_raw_secondary += entry_log["card_1_vp"]
                if entry_log["card_2_name"]: current_raw_secondary += entry_log["card_2_vp"]
                if entry_log.get("card_3_name"): current_raw_secondary += entry_log.get("card_3_vp",0) 

        scores_dict[player_key]["raw_secondary"] = current_raw_secondary
        scores_dict[player_key]["capped_secondary"] = min(scores_dict[player_key]["raw_secondary"], MAX_TOTAL_SECONDARY_VP)
        if st.session_state.paint_vp_bonus_selected: 
            scores_dict[player_key]["paint_vp"] = PAINT_BONUS_VP
        scores_dict[player_key]["total"] = scores_dict[player_key]["capped_primary"] + \
                                           scores_dict[player_key]["capped_secondary"] + \
                                           scores_dict[player_key]["paint_vp"]
    return scores_dict

def run_monte_carlo_for_future_secondaries(player_type, num_simulations, 
                                           current_game_turn_sim, current_active_player_sim, 
                                           actual_current_hand_sim, game_log_sim):
    total_sim_vp_accumulator = 0.0

    for _ in range(num_simulations):
        sim_run_vp = 0.0
        
        # Cards used by THIS player in the main game log for this simulation run
        cards_used_by_sim_player_this_run = set()
        for entry in game_log_sim:
            if entry['player_type'] == player_type: 
                if entry.get("final_hand_after_mulligan_or_selection"):
                    for card_used in entry["final_hand_after_mulligan_or_selection"]:
                        if card_used: cards_used_by_sim_player_this_run.add(card_used)
                elif entry.get("card_1_name"): cards_used_by_sim_player_this_run.add(entry["card_1_name"])
                elif entry.get("card_2_name"): cards_used_by_sim_player_this_run.add(entry["card_2_name"])


        player_initial_active_deck = st.session_state.user_active_deck if player_type == "user" else st.session_state.opponent_active_deck
        mulliganed_by_this_player = st.session_state.mulliganed_cards_by_player.get(player_type, set())
        
        sim_initial_available_deck = [
            card for card in player_initial_active_deck 
            if card not in cards_used_by_sim_player_this_run and \
               card not in mulliganed_by_this_player and \
               card not in (actual_current_hand_sim or [])
        ]
        
        logged_turns_for_player = set(entry['game_turn'] for entry in game_log_sim if entry['player_type'] == player_type)
        num_secondary_phases_completed = len(logged_turns_for_player)
        is_current_hand_active_for_player = (
            current_active_player_sim == player_type and 
            actual_current_hand_sim and 
            current_game_turn_sim not in logged_turns_for_player 
        )
        opportunities_already_accounted_for = num_secondary_phases_completed
        if is_current_hand_active_for_player:
            opportunities_already_accounted_for += 1
        num_future_draw_opportunities = MAX_GAME_TURNS - opportunities_already_accounted_for
        
        available_cards_this_sim_iteration = list(sim_initial_available_deck) 
        
        for i in range(num_future_draw_opportunities):
            if not available_cards_this_sim_iteration or len(available_cards_this_sim_iteration) < 1:
                break 
            player_scoring_turn_index = opportunities_already_accounted_for + 1 + i 
            prob_lookup_game_turn = min(player_scoring_turn_index, MAX_GAME_TURNS) 

            num_to_draw_sim = min(2, len(available_cards_this_sim_iteration)) 
            drawn_sim_cards = random.sample(available_cards_this_sim_iteration, num_to_draw_sim)

            for card_s in drawn_sim_cards:
                if card_s in available_cards_this_sim_iteration: 
                    available_cards_this_sim_iteration.remove(card_s) 
                if card_s in CARDS_DATA and card_s in st.session_state.probabilities[player_type]:
                    for comp_s in CARDS_DATA[card_s]["vp_components"]:
                        comp_label_s = comp_s["label"]
                        comp_vp_s = comp_s["vp"]
                        prob_s = st.session_state.probabilities[player_type][card_s][comp_label_s].get(prob_lookup_game_turn, 0.0)
                        if random.random() < prob_s: 
                            sim_run_vp += comp_vp_s
        total_sim_vp_accumulator += sim_run_vp
    
    return total_sim_vp_accumulator / num_simulations if num_simulations > 0 else 0.0


def calculate_projected_scores(): 
    current_scores_data = calculate_total_scores() 
    mc_projection_results = st.session_state.get('monte_carlo_projection', None)
    projected_display_totals = {}

    for p_type_proj in ["user", "opponent"]:
        if mc_projection_results and p_type_proj in mc_projection_results: 
            projected_display_totals[p_type_proj] = mc_projection_results[p_type_proj]
        else: 
            projected_display_totals[p_type_proj] = current_scores_data[p_type_proj]["total"]
    return projected_display_totals


def run_and_store_monte_carlo_projections():
    num_sims = st.session_state.num_mc_simulations
    current_scores = calculate_total_scores() 
    
    st.session_state.monte_carlo_projection = {"user": 0.0, "opponent": 0.0}

    for p_type_proj in ["user", "opponent"]:
        current_capped_primary = current_scores[p_type_proj]["capped_primary"]
        projected_raw_secondary = current_scores[p_type_proj]["raw_secondary"] 
        current_hand_ev = 0
        active_player_current_hand = st.session_state.current_player_final_hand if \
            (st.session_state.active_player_type == p_type_proj and st.session_state.turn_segment_in_progress) else None
        
        if active_player_current_hand: 
            current_hand_ev = calculate_hand_ev(
                active_player_current_hand, p_type_proj, 
                st.session_state.current_game_turn, 
                use_overrides=(p_type_proj == "user") 
            )
        projected_raw_secondary += current_hand_ev
        
        ev_future_undrawn = run_monte_carlo_for_future_secondaries(
            p_type_proj, num_sims, 
            st.session_state.current_game_turn,
            st.session_state.active_player_type, 
            active_player_current_hand, 
            st.session_state.game_log
        )
        projected_raw_secondary += ev_future_undrawn
        final_projected_capped_secondary = min(projected_raw_secondary, MAX_TOTAL_SECONDARY_VP)
        paint_vp_value = PAINT_BONUS_VP if st.session_state.paint_vp_bonus_selected else 0
        st.session_state.monte_carlo_projection[p_type_proj] = current_capped_primary + final_projected_capped_secondary + paint_vp_value


# --- UI Display Functions ---

def display_setup_screen():
    st.header("Game Setup")

    key_setup_user_goes_first = "widget_setup_user_goes_first"
    key_setup_paint_bonus = "widget_setup_paint_bonus"
    key_setup_user_removed_card = "widget_setup_user_removed_card_radio"
    key_setup_opponent_removed_card = "widget_setup_opponent_removed_card_radio"
    key_setup_reset_probs = "widget_reset_probs_on_new_game"

    if st.session_state.get('show_confirm_new_game_setup', False):
        st.warning("Are you sure you want to start a new game with the selected settings? This will reset any current progress if a game was previously active.")
        col1, col2 = st.columns(2)
        if col1.button("Yes, Start New Game", key="confirm_yes_setup"):
            start_new_game() 
            st.session_state.show_confirm_new_game_setup = False
            st.rerun()
        if col2.button("No, Cancel", key="confirm_no_setup"):
            st.session_state.show_confirm_new_game_setup = False
            st.rerun()
    else:
        st.checkbox("I will go first", value=st.session_state.get(key_setup_user_goes_first, True), key=key_setup_user_goes_first)
        st.checkbox(f"Start with {PAINT_BONUS_VP} 'Battle Ready' VP (Paint Bonus)", 
                    value=st.session_state.get(key_setup_paint_bonus, False), key=key_setup_paint_bonus)
        
        removal_options = ["Keep Both", "Remove Cull the Horde", "Remove Bring It Down"]
        
        st.radio(
            "User's Deck: Optional Card Removal:", options=removal_options,
            index=removal_options.index(st.session_state.get("user_removed_card_option", "Keep Both")), 
            key=key_setup_user_removed_card 
        )
        st.radio(
            "Opponent's Deck: Optional Card Removal:", options=removal_options,
            index=removal_options.index(st.session_state.get("opponent_removed_card_option", "Keep Both")), 
            key=key_setup_opponent_removed_card
        )

        st.checkbox("Reset card probabilities to default on new game start", 
                    value=st.session_state.get(key_setup_reset_probs, True), key=key_setup_reset_probs)
        
        if st.button("Start Game", key="initiate_start_game_setup"):
            st.session_state.setup_user_goes_first = st.session_state[key_setup_user_goes_first]
            st.session_state.setup_paint_vp_bonus = st.session_state[key_setup_paint_bonus]
            st.session_state.setup_user_removed_card_option = st.session_state[key_setup_user_removed_card]
            st.session_state.setup_opponent_removed_card_option = st.session_state[key_setup_opponent_removed_card]
            st.session_state.setup_reset_probs_on_new_game = st.session_state[key_setup_reset_probs]

            st.session_state.show_confirm_new_game_setup = True
            st.rerun()


def display_scoreboard_and_projections():
    scores_display_obj = calculate_total_scores() 
    st.sidebar.header("Scoreboard")
    for player_s_type in ["user", "opponent"]: 
        player_s_label = "Your" if player_s_type == "user" else "Opponent's"
        score_details_str = (f"P: {scores_display_obj[player_s_type]['capped_primary']}/{MAX_TOTAL_PRIMARY_VP}, "
                             f"S: {scores_display_obj[player_s_type]['capped_secondary']}/{MAX_TOTAL_SECONDARY_VP}")
        if st.session_state.paint_vp_bonus_selected: 
            score_details_str += f", Paint: {PAINT_BONUS_VP}"
        st.sidebar.write(f"**{player_s_label} VP: {scores_display_obj[player_s_type]['total']}** ({score_details_str})")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Monte Carlo Projected Scores")
    
    sim_count_options = [5000, 10000] 
    current_sim_count = st.session_state.get('num_mc_simulations', 5000)
    if current_sim_count not in sim_count_options:
        current_sim_count = 5000 
        st.session_state.num_mc_simulations = current_sim_count

    st.session_state.num_mc_simulations = st.sidebar.radio(
        "Number of Simulations:", options=sim_count_options,
        index=sim_count_options.index(current_sim_count),
        key="mc_sim_count_radio"
    )

    if st.sidebar.button("Run VP Projection Simulation", key="run_mc_button"):
        with st.spinner(f"Running {st.session_state.num_mc_simulations} simulations... This may take a moment."):
            run_and_store_monte_carlo_projections()
        st.rerun() 

    projected_scores_display = calculate_projected_scores() 

    if st.session_state.get('monte_carlo_projection') is not None:
        st.sidebar.write(f"Your Projected Total VP: **{projected_scores_display['user']:.1f}**")
        st.sidebar.write(f"Opponent's Projected Total VP: **{projected_scores_display['opponent']:.1f}**")
        st.sidebar.caption(f"(Based on {st.session_state.num_mc_simulations} simulations)")
    else: 
        st.sidebar.write(f"Your Projected Total VP: **{scores_display_obj['user']['total']:.1f}** (Current)")
        st.sidebar.write(f"Opponent's Projected Total VP: **{scores_display_obj['opponent']['total']:.1f}** (Current)")
        st.sidebar.caption("(Run simulation for full projection)")


def display_current_turn_interface():
    active_player_name_full = "Your" if st.session_state.active_player_type == "user" else "Opponent's"
    active_player_name_short = "You" if st.session_state.active_player_type == "user" else "Opponent"
    st.header(f"Game Turn {st.session_state.current_game_turn} - {active_player_name_full} Actions")
    current_game_turn_idx = st.session_state.current_game_turn - 1 

    st.subheader("0. Log Primary VP for this Turn")
    current_primary_score_for_turn = st.session_state.all_primary_vps[st.session_state.active_player_type][current_game_turn_idx]
    new_primary_score_for_turn = st.number_input(
        f"Primary VP scored by {active_player_name_short.lower()} in Turn {st.session_state.current_game_turn} (0-{MAX_PRIMARY_VP_PER_TURN_INPUT}):",
        min_value=0, max_value=MAX_PRIMARY_VP_PER_TURN_INPUT, value=current_primary_score_for_turn,
        key=f"current_primary_vp_input_{st.session_state.active_player_type}_{st.session_state.current_game_turn}"
    )
    if new_primary_score_for_turn != current_primary_score_for_turn:
        st.session_state.all_primary_vps[st.session_state.active_player_type][current_game_turn_idx] = new_primary_score_for_turn
    st.markdown("---") 
    if not st.session_state.turn_segment_in_progress: 
        st.subheader("1. Choose Secondary Cards for this Turn")
        card_selection_method = st.radio(
            "Card Selection Method:", 
            ("Randomly Draw 2 Cards", "Select Used Cards (up to 3)"), 
            key=f"card_selection_method_{st.session_state.active_player_type}_{st.session_state.current_game_turn}"
        )
        
        current_deck_available = get_available_deck(st.session_state.active_player_type) 
        
        if card_selection_method == "Randomly Draw 2 Cards":
            num_cards_can_draw = min(2, len(current_deck_available))
            draw_button_label = f"Draw {num_cards_can_draw} Card(s)" if num_cards_can_draw > 0 else "Deck Empty"
            if st.button(draw_button_label, 
                         key=f"random_draw_button_{st.session_state.active_player_type}", 
                         disabled=(num_cards_can_draw == 0)): 
                draw_initial_cards_for_player(st.session_state.active_player_type, num_cards_to_draw=num_cards_can_draw)
                st.rerun() 
        else: # "Select Used Cards (up to 3)"
            if not current_deck_available: st.warning("No cards left in deck to select.")
            else:
                num_can_select_manual = min(3, len(current_deck_available)) 
                manually_selected_cards = st.multiselect(f"Select up to {num_can_select_manual} card(s):", 
                                                           current_deck_available, max_selections=num_can_select_manual, 
                                                           key=f"manual_card_selection_{st.session_state.active_player_type}")
                if st.button("Confirm Selection", key=f"confirm_manual_selection_button_{st.session_state.active_player_type}"):
                    if len(manually_selected_cards) <= num_can_select_manual: 
                         if manually_select_cards_for_player(st.session_state.active_player_type, manually_selected_cards, max_cards=3):
                            st.rerun() 
        return 
    
    initially_drawn_hand = st.session_state.current_player_drawn_cards 
    st.subheader("2. Initial Hand & Mulligan Option")
    st.write("Cards initially drawn/selected for this turn:")
    if initially_drawn_hand:
        for card_item in initially_drawn_hand: st.markdown(f"- **{card_item}**")
    else:
        st.write("No cards were drawn or selected for this turn.")

    st.markdown("---")
    st.subheader(f"Remaining Cards in {active_player_name_full} Deck")
    active_player_deck_remaining = get_available_deck(st.session_state.active_player_type)
    active_player_deck_remaining_for_display = [card for card in active_player_deck_remaining if card not in initially_drawn_hand]
    if active_player_deck_remaining_for_display:
        num_cols_deck_display = 4 
        card_cols_deck_display = st.columns(num_cols_deck_display)
        for idx, card_name_remaining in enumerate(sorted(active_player_deck_remaining_for_display)): 
            with card_cols_deck_display[idx % num_cols_deck_display]:
                st.caption(card_name_remaining)
    else:
        st.caption("No cards remaining in deck.")
    st.markdown("---")
    
    if st.session_state.active_player_type == "user" and initially_drawn_hand:
        ev_initial = calculate_hand_ev(initially_drawn_hand, "user", st.session_state.current_game_turn, use_overrides=False)
        st.info(f"EV of initial hand (default probs): {ev_initial:.2f}. {get_ev_recommendation(ev_initial)}")

    if initially_drawn_hand: 
        cards_selected_for_mulligan = st.multiselect("Select cards from initial hand to discard & redraw (mulligan):", 
                                                     initially_drawn_hand, 
                                                     key=f"mulligan_selection_{st.session_state.active_player_type}")
        if st.button("Confirm Mulligan / Keep Initial Hand", key=f"mulligan_confirm_button_{st.session_state.active_player_type}"):
            if cards_selected_for_mulligan: mulligan_cards(st.session_state.active_player_type, cards_selected_for_mulligan) 
            st.session_state.current_turn_component_prob_overrides = {} 
            st.rerun() 
    
    st.markdown("---") 
    final_hand_to_score = st.session_state.current_player_final_hand
    st.subheader("3. Final Hand for Scoring This Turn")    
    if not final_hand_to_score: st.write("No cards in final hand to score.")
    else:
        for card_name_final in final_hand_to_score: st.markdown(f"- **{card_name_final}**")

    if st.session_state.active_player_type == "user" and final_hand_to_score:
        st.markdown("---")
        st.subheader("3a. Estimate Scoring Probabilities for Final Hand (This Turn Only)")
        for card_in_final_hand in final_hand_to_score: 
            if card_in_final_hand not in st.session_state.current_turn_component_prob_overrides:
                st.session_state.current_turn_component_prob_overrides[card_in_final_hand] = {}

        for card_name_override in final_hand_to_score:
            if card_name_override in CARDS_DATA and card_name_override in st.session_state.probabilities["user"]:
                st.markdown(f"**Override probabilities for: {card_name_override}**")
                for component_override in CARDS_DATA[card_name_override].get("vp_components", []):
                    comp_label_override = component_override["label"]
                    default_prob_for_slider = st.session_state.probabilities["user"] \
                        .get(card_name_override, {}).get(comp_label_override, {}) \
                        .get(st.session_state.current_game_turn, 0.6) 
                    
                    current_override_val = st.session_state.current_turn_component_prob_overrides[card_name_override].get(comp_label_override, default_prob_for_slider)

                    estimated_prob = st.slider(
                        f"{comp_label_override}", 0.0, 1.0, current_override_val, step=0.01,
                        key=f"override_prob_{card_name_override}_{comp_label_override.replace(' ','_')}_{st.session_state.current_game_turn}",
                        format="%.2f" # Display as float, can be changed to "%.0f%%" for percentage
                    )
                    st.session_state.current_turn_component_prob_overrides[card_name_override][comp_label_override] = estimated_prob
        
        ev_final_override = calculate_hand_ev(final_hand_to_score, "user", st.session_state.current_game_turn, use_overrides=True)
        st.info(f"EV of final hand (with your estimates): {ev_final_override:.2f}. {get_ev_recommendation(ev_final_override)}")


    st.markdown("---") 
    st.subheader("4. Input Secondary VPs") 
    for card_name_scoring in final_hand_to_score: 
        if card_name_scoring not in st.session_state.current_player_card_vps: 
            st.session_state.current_player_card_vps[card_name_scoring] = 0
        
        st.session_state.current_player_card_vps[card_name_scoring] = st.number_input(
            f"VP for '{card_name_scoring}'", 0, VP_PER_SECONDARY_CARD_INPUT_MAX, 
            value=st.session_state.current_player_card_vps.get(card_name_scoring,0), 
            key=f"vp_input_{card_name_scoring}_{st.session_state.active_player_type}_{st.session_state.current_game_turn}"
        )
    st.markdown("---") 
    if st.button(f"End {active_player_name_full} Actions & Log Turn", 
                 key=f"log_turn_button_{st.session_state.active_player_type}"):
        log_player_turn() 
        st.rerun() 

def display_probability_settings():
    st.header("Adjust Card Scoring Probabilities")
    st.caption("Probabilities (per round T1-T5) for each scoring component affect the User's hand EV.")
    st.markdown("---") 
    
    user_tab, opponent_tab = st.tabs(["User's Probabilities", "Opponent's Probabilities"])
    
    for player_type_ui, tab_ui, active_deck_ui in [("user", user_tab, st.session_state.user_active_deck), 
                                                   ("opponent", opponent_tab, st.session_state.opponent_active_deck)]:
        with tab_ui:
            cards_logged_by_this_player_set = get_cards_logged_by_player(player_type_ui)
            mulliganed_by_this_player_set = st.session_state.mulliganed_cards_by_player.get(player_type_ui, set())

            sorted_cards_in_player_active_deck = sorted([card for card in active_deck_ui if card in CARDS_DATA])
            
            cards_to_display_probs_for = [
                card for card in sorted_cards_in_player_active_deck 
                if card not in cards_logged_by_this_player_set and card not in mulliganed_by_this_player_set
            ]

            if not cards_to_display_probs_for:
                st.write(f"All cards in {player_type_ui.capitalize()}'s active deck have been used, mulliganed, or the deck is empty.")
            
            for card_name_tab in cards_to_display_probs_for:
                if card_name_tab not in st.session_state.probabilities[player_type_ui]:
                    st.session_state.probabilities[player_type_ui][card_name_tab] = \
                        copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES["user"].get(card_name_tab, {}))
                
                with st.expander(f"{card_name_tab}", expanded=False): 
                    if card_name_tab in st.session_state.probabilities[player_type_ui]:
                        for component_tab_data in CARDS_DATA[card_name_tab].get("vp_components", []):
                            comp_label_tab = component_tab_data["label"]
                            comp_vp_val = component_tab_data["vp"]
                            st.markdown(f"**{comp_label_tab} ({comp_vp_val} VP)**")
                            
                            if comp_label_tab not in st.session_state.probabilities[player_type_ui][card_name_tab]:
                                st.session_state.probabilities[player_type_ui][card_name_tab][comp_label_tab] = \
                                    copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES["user"].get(card_name_tab,{}).get(comp_label_tab, {r:0.6 for r in range(1,MAX_GAME_TURNS+1)}))

                            slider_cols_prob = st.columns(MAX_GAME_TURNS)
                            for r_idx_ui, col_ui in enumerate(slider_cols_prob):
                                game_round_ui = r_idx_ui + 1
                                current_prob_ui = st.session_state.probabilities[player_type_ui][card_name_tab][comp_label_tab].get(game_round_ui, 0.0)
                                new_prob_ui = col_ui.slider(f"T{game_round_ui}", 0.0, 1.0, current_prob_ui, step=0.01, 
                                                            key=f"prob_slider_{player_type_ui}_{card_name_tab}_{comp_label_tab.replace(' ','_')}_r{game_round_ui}", 
                                                            label_visibility="collapsed", format="%.2f") # Display as float, can be "%.0f%%"
                                if new_prob_ui != current_prob_ui: 
                                    st.session_state.probabilities[player_type_ui][card_name_tab][comp_label_tab][game_round_ui] = new_prob_ui
                        st.markdown("---") 
                    else: 
                        st.caption(f"Probability data for '{card_name_tab}' not found for {player_type_ui}.")


def display_all_primary_vp_input():
    with st.expander(f"Edit All Primary VPs (Max {MAX_TOTAL_PRIMARY_VP} total from objectives, {MAX_PRIMARY_VP_PER_TURN_INPUT}/turn input limit)", expanded=False):
        for player_type_vp_edit in ["user", "opponent"]: 
            st.subheader(f"{player_type_vp_edit.capitalize()}'s Primary VPs (Turns 1-5)")
            vp_input_cols = st.columns(MAX_GAME_TURNS) 
            for turn_idx_vp_edit, col_vp_edit in enumerate(vp_input_cols):
                turn_num_display = turn_idx_vp_edit + 1 
                current_vp_val = st.session_state.all_primary_vps[player_type_vp_edit][turn_idx_vp_edit]
                new_vp_val = col_vp_edit.number_input(f"T{turn_num_display}", 0, MAX_PRIMARY_VP_PER_TURN_INPUT, 
                                                      value=current_vp_val,
                                                      key=f"all_primary_vp_edit_{player_type_vp_edit}_t{turn_num_display}", 
                                                      label_visibility="collapsed") 
                if new_vp_val != current_vp_val: 
                    st.session_state.all_primary_vps[player_type_vp_edit][turn_idx_vp_edit] = new_vp_val
        if st.button("Refresh Scores After Primary VP Edits", key="refresh_primary_vp_edits_button"): 
            st.rerun()

def display_edit_past_scores(): 
    with st.expander("Edit Past Secondary Scores / Game Log Details", expanded=False):
        if not st.session_state.game_log: st.write("No game turns have been logged yet."); return 
        for log_idx, logged_turn_data in reversed(list(enumerate(st.session_state.game_log))):
            player_label_log = logged_turn_data['player_type'].capitalize()
            st.markdown(f"---") 
            st.markdown(f"**Turn {logged_turn_data['game_turn']} - {player_label_log}** (Log ID: ...{logged_turn_data['log_id'][-6:]})") 
            st.write(f"Primary VP logged for this player's actions in this turn: {logged_turn_data['primary_vp_logged_for_turn']}")
            for card_num_str, card_prefix_key in [("1", "card_1"), ("2", "card_2"), ("3", "card_3")]: 
                card_name_key_log = f"{card_prefix_key}_name"
                card_vp_key_log = f"{card_prefix_key}_vp"
                if logged_turn_data.get(card_name_key_log): 
                    st.markdown(f"**Card: {logged_turn_data[card_name_key_log]}**")
                    new_card_vp_log = st.number_input(f"VP Scored", 0, VP_PER_SECONDARY_CARD_INPUT_MAX, 
                                                      value=logged_turn_data[card_vp_key_log], 
                                                      key=f"edit_vp_{card_vp_key_log}_{logged_turn_data['log_id']}")
                    if new_card_vp_log != logged_turn_data[card_vp_key_log]: 
                        st.session_state.game_log[log_idx][card_vp_key_log] = new_card_vp_log
        if st.button("Refresh Scores After Log Edits", key="refresh_secondary_log_edits_button"): 
            st.rerun()

# --- Main Application Flow ---
def main():
    st.set_page_config(layout="wide") 
    st.title("Warhammer 40k Game Simulator & Tracker") 

    if 'setup_user_removed_card_option' not in st.session_state: 
        st.session_state.setup_user_removed_card_option = "Keep Both"
    if 'setup_opponent_removed_card_option' not in st.session_state:
        st.session_state.setup_opponent_removed_card_option = "Keep Both"
    if 'show_confirm_new_game_setup' not in st.session_state: 
        st.session_state.show_confirm_new_game_setup = False
    if 'show_confirm_new_game_sidebar' not in st.session_state:
        st.session_state.show_confirm_new_game_sidebar = False
        
    initialize_session_state() 

    if not st.session_state.game_started: 
        display_setup_screen()
    else: 
        display_scoreboard_and_projections() 
        if st.session_state.current_game_turn > MAX_GAME_TURNS: 
            st.header("Game Over!")
            st.balloons() 
            if st.button("Start New Game", key="game_over_start_new_game_button"): 
                st.session_state.show_confirm_new_game_sidebar = True 
                st.rerun()
        else: 
            display_current_turn_interface() 
        
        st.markdown("---"); display_all_primary_vp_input() 
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Probability CSV Management")
        # User CSV Download
        user_active_deck_for_csv = st.session_state.user_active_deck
        user_probs_csv_data = []
        for card_name_csv in user_active_deck_for_csv: 
            if card_name_csv in st.session_state.probabilities["user"] and card_name_csv in CARDS_DATA:
                for component in CARDS_DATA[card_name_csv].get("vp_components", []):
                    comp_label_csv = component["label"]
                    row_data = {"Card Name": card_name_csv, "Component Label": comp_label_csv}
                    comp_probs_csv = st.session_state.probabilities["user"][card_name_csv].get(comp_label_csv, {})
                    for r_csv in range(1, MAX_GAME_TURNS + 1):
                        row_data[f"Round {r_csv}"] = comp_probs_csv.get(r_csv, 0.0)
                    user_probs_csv_data.append(row_data)
        if user_probs_csv_data:
            user_probs_df = pd.DataFrame(user_probs_csv_data)
            st.sidebar.download_button(label="Download User Probabilities (CSV)", 
                               data=user_probs_df.to_csv(index=False).encode('utf-8'),
                               file_name="user_card_probabilities.csv", mime="text/csv", 
                               key="sidebar_download_user_probabilities_csv_button")
        else: st.sidebar.info("User's deck empty for CSV download.")

        # User CSV Upload
        csv_upload_file_sidebar_user = st.sidebar.file_uploader("Upload User Probabilities (CSV File)", type="csv", 
                                           key="sidebar_upload_user_probabilities_csv_uploader")
        if csv_upload_file_sidebar_user is not None:
            try:
                uploaded_df_sidebar = pd.read_csv(csv_upload_file_sidebar_user)
                new_parsed_probs_user_sidebar = {}
                for card_name_parse_sb in st.session_state.user_active_deck: 
                    if card_name_parse_sb in CARDS_DATA:
                        new_parsed_probs_user_sidebar[card_name_parse_sb] = {}
                        for component_parse_sb in CARDS_DATA[card_name_parse_sb].get("vp_components",[]):
                            comp_label_parse_sb = component_parse_sb["label"]
                            default_comp_probs_sb = ROUND_BASED_DEFAULT_PROBABILITIES["user"].get(card_name_parse_sb,{}).get(comp_label_parse_sb,{r:0.6 for r in range(1,MAX_GAME_TURNS+1)})
                            new_parsed_probs_user_sidebar[card_name_parse_sb][comp_label_parse_sb] = copy.deepcopy(default_comp_probs_sb)
                for _, csv_row_sb in uploaded_df_sidebar.iterrows():
                    card_name_from_csv_sb = csv_row_sb.get("Card Name")
                    comp_label_from_csv_sb = csv_row_sb.get("Component Label")
                    if card_name_from_csv_sb in new_parsed_probs_user_sidebar and \
                       comp_label_from_csv_sb in new_parsed_probs_user_sidebar.get(card_name_from_csv_sb, {}):
                        for r_from_csv_sb in range(1, MAX_GAME_TURNS + 1):
                            col_name_sb = f"Round {r_from_csv_sb}"
                            if col_name_sb in csv_row_sb:
                                try: new_parsed_probs_user_sidebar[card_name_from_csv_sb][comp_label_from_csv_sb][r_from_csv_sb] = float(csv_row_sb[col_name_sb])
                                except ValueError: pass 
                st.session_state.probabilities["user"] = new_parsed_probs_user_sidebar
                st.sidebar.success("User probabilities successfully uploaded!"); st.rerun() 
            except Exception as e_csv_sb: st.sidebar.error(f"Error processing User CSV: {e_csv_sb}")

        # Opponent CSV Upload
        csv_upload_file_sidebar_opp = st.sidebar.file_uploader("Upload Opponent Probabilities (CSV File)", type="csv", 
                                           key="sidebar_upload_opponent_probabilities_csv_uploader")
        if csv_upload_file_sidebar_opp is not None:
            try:
                uploaded_df_sidebar_opp = pd.read_csv(csv_upload_file_sidebar_opp)
                new_parsed_probs_opp_sidebar = {}
                for card_name_parse_sb_opp in st.session_state.opponent_active_deck: 
                    if card_name_parse_sb_opp in CARDS_DATA:
                        new_parsed_probs_opp_sidebar[card_name_parse_sb_opp] = {}
                        for component_parse_sb_opp in CARDS_DATA[card_name_parse_sb_opp].get("vp_components",[]):
                            comp_label_parse_sb_opp = component_parse_sb_opp["label"]
                            default_comp_probs_sb_opp = ROUND_BASED_DEFAULT_PROBABILITIES["opponent"].get(card_name_parse_sb_opp,{}).get(comp_label_parse_sb_opp,{r:0.6 for r in range(1,MAX_GAME_TURNS+1)})
                            new_parsed_probs_opp_sidebar[card_name_parse_sb_opp][comp_label_parse_sb_opp] = copy.deepcopy(default_comp_probs_sb_opp)
                for _, csv_row_sb_opp in uploaded_df_sidebar_opp.iterrows():
                    card_name_from_csv_sb_opp = csv_row_sb_opp.get("Card Name")
                    comp_label_from_csv_sb_opp = csv_row_sb_opp.get("Component Label")
                    if card_name_from_csv_sb_opp in new_parsed_probs_opp_sidebar and \
                       comp_label_from_csv_sb_opp in new_parsed_probs_opp_sidebar.get(card_name_from_csv_sb_opp, {}):
                        for r_from_csv_sb_opp in range(1, MAX_GAME_TURNS + 1):
                            col_name_sb_opp = f"Round {r_from_csv_sb_opp}"
                            if col_name_sb_opp in csv_row_sb_opp:
                                try: new_parsed_probs_opp_sidebar[card_name_from_csv_sb_opp][comp_label_from_csv_sb_opp][r_from_csv_sb_opp] = float(csv_row_sb_opp[col_name_sb_opp])
                                except ValueError: pass 
                st.session_state.probabilities["opponent"] = new_parsed_probs_opp_sidebar
                st.sidebar.success("Opponent probabilities successfully uploaded!"); st.rerun() 
            except Exception as e_csv_sb_opp: st.sidebar.error(f"Error processing Opponent CSV: {e_csv_sb_opp}")


        st.markdown("---"); display_probability_settings() 
        st.markdown("---"); display_edit_past_scores() 
        
        st.sidebar.markdown("---")
        if st.session_state.get('show_confirm_new_game_sidebar', False):
            st.sidebar.warning("Discard current game and start new?")
            col_sb1, col_sb2 = st.sidebar.columns(2)
            if col_sb1.button("Yes, Discard", key="confirm_yes_sidebar"):
                st.session_state.game_started = False 
                st.session_state.setup_user_removed_card_option = "Keep Both" 
                st.session_state.setup_opponent_removed_card_option = "Keep Both"
                initialize_session_state() 
                st.session_state.show_confirm_new_game_sidebar = False
                st.rerun()
            if col_sb2.button("No, Keep Playing", key="confirm_no_sidebar"):
                st.session_state.show_confirm_new_game_sidebar = False
                st.rerun()
        elif st.sidebar.button("Start New Game (Resets Current Progress)", key="sidebar_start_new_game_button"):
            st.session_state.show_confirm_new_game_sidebar = True
            st.rerun()


if __name__ == "__main__":
    main()
