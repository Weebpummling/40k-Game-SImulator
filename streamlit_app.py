import streamlit as st
import random
import copy
import uuid
import pandas as pd
import io

# --- Constants and Configuration ---
CARDS_DATA = {
    "Assassination": {"first_turn_restricted": False, "default_vp_potential": 5},
    "Containment": {"first_turn_restricted": False, "default_vp_potential": 3},
    "Behind Enemy Lines": {"first_turn_restricted": False, "default_vp_potential": 3},
    "Marked for Death": {"first_turn_restricted": False, "default_vp_potential": 5},
    "Bring It Down": {"first_turn_restricted": False, "default_vp_potential": 2},
    "No Prisoners": {"first_turn_restricted": False, "default_vp_potential": 2},
    "Defend Stronghold": {"first_turn_restricted": True, "default_vp_potential": 3},
    "Storm Hostile Objective": {"first_turn_restricted": False, "default_vp_potential": 4},
    "Sabotage": {"first_turn_restricted": False, "default_vp_potential": 3},
    "Cull the Horde": {"first_turn_restricted": False, "default_vp_potential": 5},
    "Overwhelming Force": {"first_turn_restricted": False, "default_vp_potential": 3},
    "Extend Battle Lines": {"first_turn_restricted": False, "default_vp_potential": 5},
    "Recover Assets": {"first_turn_restricted": False, "default_vp_potential": 3},
    "Engage on All Fronts": {"first_turn_restricted": False, "default_vp_potential": 2},
    "Area Denial": {"first_turn_restricted": False, "default_vp_potential": 2},
    "Secure No Man's Land": {"first_turn_restricted": True, "default_vp_potential": 2},
    "Cleanse": {"first_turn_restricted": False, "default_vp_potential": 2},
    "Establish Locus": {"first_turn_restricted": False, "default_vp_potential": 2},
    "Capture Enemy Outpost": {"first_turn_restricted": False, "default_vp_potential": 4},
    "Investigate Signals": {"first_turn_restricted": False, "default_vp_potential": 4},
    "Retrieve Battlefield Data": {"first_turn_restricted": False, "default_vp_potential": 4},
}

MASTER_DECK = list(CARDS_DATA.keys())
MAX_GAME_TURNS = 5
VP_PER_SECONDARY_CARD_MAX = 5 
MAX_PRIMARY_VP_PER_TURN_INPUT = 15 # Max a player can input for a single turn's primary objectives
MAX_TOTAL_PRIMARY_VP = 50 # Max total primary VP from game actions (excluding paint)
MAX_TOTAL_SECONDARY_VP = 40 # Max total secondary VP
PAINT_BONUS_VP = 10

ROUND_BASED_DEFAULT_PROBABILITIES = {
    "user": {
        "Assassination":           {1: 0.20, 2: 0.30, 3: 0.50, 4: 0.70, 5: 0.80},
        "Containment":             {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
        "Behind Enemy Lines":      {1: 0.00, 2: 0.10, 3: 0.30, 4: 0.50, 5: 0.80},
        "Marked for Death":        {1: 0.00, 2: 0.00, 3: 0.20, 4: 0.30, 5: 0.50},
        "Bring It Down":           {1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.80},
        "No Prisoners":            {1: 0.20, 2: 0.80, 3: 1.00, 4: 1.00, 5: 1.00},
        "Defend Stronghold":       {1: 0.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00}, 
        "Storm Hostile Objective": {1: 0.00, 2: 0.50, 3: 0.80, 4: 0.80, 5: 0.50},
        "Sabotage":                {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.50, 5: 0.50},
        "Cull the Horde":          {1: 0.00, 2: 0.00, 3: 0.00, 4: 0.10, 5: 0.30},
        "Overwhelming Force":      {1: 0.10, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80},
        "Extend Battle Lines":     {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
        "Recover Assets":          {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.50, 5: 0.50},
        "Engage on All Fronts":    {1: 0.80, 2: 0.30, 3: 0.50, 4: 0.80, 5: 0.80},
        "Area Denial":             {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80},
        "Secure No Man's Land":    {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00}, 
        "Cleanse":                 {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00},
        "Establish Locus":         {1: 1.00, 2: 0.80, 3: 0.80, 4: 0.80, 5: 0.80},
    },
}
# Ensure all cards in MASTER_DECK have an entry in ROUND_BASED_DEFAULT_PROBABILITIES for the 'user'
# And then copy to 'opponent'. This loop ensures any card in MASTER_DECK not explicitly defined above gets a default.
for card_name_iter in MASTER_DECK:
    if card_name_iter not in ROUND_BASED_DEFAULT_PROBABILITIES["user"]:
        ROUND_BASED_DEFAULT_PROBABILITIES["user"][card_name_iter] = {r: 0.6 for r in range(1, MAX_GAME_TURNS + 1)}

ROUND_BASED_DEFAULT_PROBABILITIES["opponent"] = copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES["user"])

# --- Helper Functions ---

def initialize_session_state():
    # Initialize game state variables if they don't exist
    if 'game_started' not in st.session_state: st.session_state.game_started = False
    if 'user_goes_first' not in st.session_state: st.session_state.user_goes_first = True
    if 'paint_vp_bonus_selected' not in st.session_state: st.session_state.paint_vp_bonus_selected = False
    if 'current_game_turn' not in st.session_state: st.session_state.current_game_turn = 1
    if 'active_player_type' not in st.session_state: st.session_state.active_player_type = "user"
    if 'game_log' not in st.session_state: st.session_state.game_log = []
    
    # Initialize or ensure completeness of probabilities structure
    if 'probabilities' not in st.session_state:
        st.session_state.probabilities = copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES)
    else: 
        for player_type_init in ["user", "opponent"]:
            if player_type_init not in st.session_state.probabilities: # If player_type key is missing
                st.session_state.probabilities[player_type_init] = copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES[player_type_init])
            for card_name_init in MASTER_DECK: # Ensure all cards are present for the player_type
                if card_name_init not in st.session_state.probabilities[player_type_init]:
                    st.session_state.probabilities[player_type_init][card_name_init] = copy.deepcopy(
                        ROUND_BASED_DEFAULT_PROBABILITIES.get(player_type_init, {}).get(card_name_init, {r: 0.6 for r in range(1, MAX_GAME_TURNS + 1)})
                    )
                else: # Ensure all rounds are present for existing cards
                    for r_idx_init in range(1, MAX_GAME_TURNS + 1):
                        if r_idx_init not in st.session_state.probabilities[player_type_init][card_name_init]:
                             st.session_state.probabilities[player_type_init][card_name_init][r_idx_init] = \
                                ROUND_BASED_DEFAULT_PROBABILITIES.get(player_type_init, {}).get(card_name_init, {}).get(r_idx_init, 0.6)

    # Initialize storage for primary VPs per turn for each player
    if 'all_primary_vps' not in st.session_state:
        st.session_state.all_primary_vps = {"user": [0] * MAX_GAME_TURNS, "opponent": [0] * MAX_GAME_TURNS}

    # Initialize transient state variables for current player actions
    if 'current_player_drawn_cards' not in st.session_state: st.session_state.current_player_drawn_cards = []
    if 'current_player_final_hand' not in st.session_state: st.session_state.current_player_final_hand = []
    if 'current_player_card_vps' not in st.session_state: st.session_state.current_player_card_vps = {} # Stores VP scored for cards in current hand
    if 'current_player_card_returned' not in st.session_state: st.session_state.current_player_card_returned = {} # Tracks if cards are returned to deck
    if 'turn_segment_in_progress' not in st.session_state: st.session_state.turn_segment_in_progress = False # True if cards drawn, awaiting VP input

def get_permanently_used_cards():
    # Returns a list of cards that have been scored and not returned to the deck
    used_cards = set()
    for log_entry in st.session_state.game_log:
        for card_slot_key in ["card_1", "card_2"]: # Check both card slots in the log
            card_name_in_log = log_entry[f"{card_slot_key}_name"]
            card_returned_in_log = log_entry[f"{card_slot_key}_returned_to_deck"]
            if card_name_in_log and not card_returned_in_log: # If card exists and was not returned
                used_cards.add(card_name_in_log)
    return list(used_cards)

def get_available_deck():
    # Returns a list of cards available for drawing (not permanently used)
    permanently_used = get_permanently_used_cards()
    return [card for card in MASTER_DECK if card not in permanently_used]

def calculate_hand_ev(hand, player_type, game_turn):
    # Calculates the Expected Value (EV) of a given hand of cards for a player in a specific game turn
    if not hand: return 0 # No cards, no EV
    total_ev = 0
    # Access the nested probability structure: probabilities[player_type][card_name][game_turn]
    current_player_probs = st.session_state.probabilities[player_type] 
    for card_name_ev in hand:
        if card_name_ev in CARDS_DATA and card_name_ev in current_player_probs:
            # Probability of scoring this card in this specific game_turn
            prob_to_score = current_player_probs[card_name_ev].get(game_turn, 0) # Default to 0 if turn/card somehow missing
            # Potential VP from this card (base potential)
            vp_potential = CARDS_DATA[card_name_ev].get("default_vp_potential", 4) # Default if not specified
            total_ev += prob_to_score * vp_potential
    return total_ev

def get_ev_recommendation(ev_score):
    # Provides a textual recommendation based on the EV score
    if ev_score < 3.0: return "Low EV. Consider discarding and redrawing heavily."
    elif ev_score < 5.0: return "Moderate EV. Discarding and redrawing might be beneficial."
    else: return "Good EV. Keeping these cards is likely a solid choice."

def start_new_game():
    # Resets the game state to start a new game based on setup screen choices
    st.session_state.game_started = True
    st.session_state.user_goes_first = st.session_state.setup_user_goes_first # From checkbox
    st.session_state.paint_vp_bonus_selected = st.session_state.setup_paint_vp_bonus # From checkbox
    st.session_state.current_game_turn = 1 # Reset to turn 1
    st.session_state.active_player_type = "user" if st.session_state.user_goes_first else "opponent" # Set active player
    st.session_state.game_log = [] # Clear game log
    st.session_state.all_primary_vps = {"user": [0]*MAX_GAME_TURNS, "opponent": [0]*MAX_GAME_TURNS} # Reset primary VPs
    # Optionally reset probabilities to default if selected
    if 'reset_probs_on_new_game' in st.session_state and st.session_state.reset_probs_on_new_game:
        st.session_state.probabilities = copy.deepcopy(ROUND_BASED_DEFAULT_PROBABILITIES)
    reset_transient_turn_state() # Clear temporary turn data
    st.session_state.turn_segment_in_progress = False

def reset_transient_turn_state():
    # Clears temporary data related to the current player's actions within a turn segment
    st.session_state.current_player_drawn_cards = []
    st.session_state.current_player_final_hand = []
    st.session_state.current_player_card_vps = {}
    st.session_state.current_player_card_returned = {}

def draw_initial_cards_for_player(player_type_draw, num_cards_to_draw=2):
    # Draws initial cards for the player, handling Turn 1 restrictions
    current_available_deck = get_available_deck()
    drawn_cards_list = []
    drew_restricted_in_t1_fallback = False # Flag to indicate if restricted cards were drawn in T1 due to necessity

    if st.session_state.current_game_turn == 1: # Special handling for Turn 1
        # Filter deck for cards not restricted on Turn 1
        eligible_deck_t1 = [card for card in current_available_deck if not CARDS_DATA[card].get("first_turn_restricted", False)]
        if len(eligible_deck_t1) < num_cards_to_draw:
            st.warning(f"T1: Not enough non-restricted cards ({len(eligible_deck_t1)} available). Drawing what's possible.")
            drawn_cards_list = random.sample(eligible_deck_t1, len(eligible_deck_t1)) # Draw all available non-restricted
            
            if len(drawn_cards_list) < num_cards_to_draw: # If still need more, must draw restricted
                num_still_needed = num_cards_to_draw - len(drawn_cards_list)
                # Get restricted cards not already chosen (if any were)
                restricted_available_t1 = [card for card in current_available_deck if CARDS_DATA[card].get("first_turn_restricted", False) and card not in drawn_cards_list]
                
                # How many restricted cards can we actually draw
                num_restricted_to_draw = min(num_still_needed, len(restricted_available_t1))
                if num_restricted_to_draw > 0:
                    drawn_cards_list.extend(random.sample(restricted_available_t1, num_restricted_to_draw))
                    drew_restricted_in_t1_fallback = True # Set flag
        else: # Enough non-restricted cards for Turn 1
            drawn_cards_list = random.sample(eligible_deck_t1, num_cards_to_draw)
    else: # Not Turn 1
        actual_num_to_draw = min(num_cards_to_draw, len(current_available_deck)) # Cannot draw more than available
        if actual_num_to_draw < num_cards_to_draw: st.warning(f"Deck low. Drawing {actual_num_to_draw} card(s) instead of {num_cards_to_draw}.")
        if actual_num_to_draw > 0: drawn_cards_list = random.sample(current_available_deck, actual_num_to_draw)
    
    if drew_restricted_in_t1_fallback: # Display the specific warning if flag is set
        st.warning("T1 Draw: Due to deck composition, restricted card(s) were drawn.")

    st.session_state.current_player_drawn_cards = drawn_cards_list
    st.session_state.current_player_final_hand = list(drawn_cards_list) # Initial hand before mulligan
    st.session_state.turn_segment_in_progress = True # Mark that cards are drawn, awaiting next step

def manually_select_cards_for_player(selected_cards_manual):
    # Allows player to manually select cards, checking Turn 1 restrictions
    if st.session_state.current_game_turn == 1: # Check restrictions if it's Turn 1
        for card_sel in selected_cards_manual:
            if CARDS_DATA[card_sel].get("first_turn_restricted", False):
                st.error(f"Cannot select '{card_sel}' in Turn 1 (it is restricted). Please choose other cards.")
                return # Stop if an invalid card is selected
    st.session_state.current_player_drawn_cards = list(selected_cards_manual)
    st.session_state.current_player_final_hand = list(selected_cards_manual)
    st.session_state.turn_segment_in_progress = True

def mulligan_cards(cards_to_mulligan_list):
    # Handles mulligan: selected cards are removed from hand, new ones drawn
    current_hand_mulligan = st.session_state.current_player_final_hand
    for card_mulligan in cards_to_mulligan_list: # Remove cards chosen for mulligan
        if card_mulligan in current_hand_mulligan: current_hand_mulligan.remove(card_mulligan)

    num_to_redraw_mulligan = len(cards_to_mulligan_list)
    if num_to_redraw_mulligan > 0:
        # Get deck available for redraw (excluding cards still in hand or permanently used)
        deck_for_redraw = [c for c in get_available_deck() if c not in current_hand_mulligan and c not in get_permanently_used_cards()]
        
        pool_to_draw_from_mulligan = []
        if st.session_state.current_game_turn == 1: # Turn 1 mulligan restrictions
            t1_mulligan_pool = [c for c in deck_for_redraw if not CARDS_DATA[c].get("first_turn_restricted", False)]
            if len(t1_mulligan_pool) < num_to_redraw_mulligan:
                st.warning("T1 Mulligan: Limited non-restricted cards for redraw. Drawing from all available.")
                pool_to_draw_from_mulligan = deck_for_redraw # Fallback to any available card
                # A more specific warning if restricted cards are actually drawn could be added here too, similar to initial draw.
            else:
                pool_to_draw_from_mulligan = t1_mulligan_pool
        else: # Not Turn 1 mulligan
            pool_to_draw_from_mulligan = deck_for_redraw
        
        actual_redraw_count = min(num_to_redraw_mulligan, len(pool_to_draw_from_mulligan))
        if actual_redraw_count < num_to_redraw_mulligan : st.warning(f"Mulligan: Not enough cards for full redraw. Drawing {actual_redraw_count}.")
        if actual_redraw_count > 0 : current_hand_mulligan.extend(random.sample(pool_to_draw_from_mulligan, actual_redraw_count))
    st.session_state.current_player_final_hand = current_hand_mulligan # Update the final hand

def log_player_turn():
    # Logs the outcome of the active player's turn segment to the game_log
    log_entry_id = str(uuid.uuid4()) # Unique ID for the log entry
    active_player = st.session_state.active_player_type
    final_hand_log = st.session_state.current_player_final_hand
    current_game_turn_idx = st.session_state.current_game_turn - 1 # 0-indexed for list access
    
    # Primary VP for this specific turn segment (already input by user for this turn)
    primary_vp_for_log = st.session_state.all_primary_vps[active_player][current_game_turn_idx]
    
    # Initialize card data for logging
    card1_name_log, card1_vp_log, card1_returned_log = None, 0, False
    card2_name_log, card2_vp_log, card2_returned_log = None, 0, False

    if len(final_hand_log) > 0: # Data for the first card
        card1_name_log = final_hand_log[0]
        card1_vp_log = st.session_state.current_player_card_vps.get(card1_name_log, 0)
        card1_returned_log = st.session_state.current_player_card_returned.get(card1_name_log, False)
    if len(final_hand_log) > 1: # Data for the second card
        card2_name_log = final_hand_log[1]
        card2_vp_log = st.session_state.current_player_card_vps.get(card2_name_log, 0)
        card2_returned_log = st.session_state.current_player_card_returned.get(card2_name_log, False)

    # Construct the log entry
    new_log_entry = {
        "log_id": log_entry_id, "game_turn": st.session_state.current_game_turn, "player_type": active_player,
        "primary_vp_logged_for_turn": primary_vp_for_log, # This is the 0-15 input for this turn
        "card_1_name": card1_name_log, "card_1_vp": card1_vp_log, "card_1_returned_to_deck": card1_returned_log,
        "card_2_name": card2_name_log, "card_2_vp": card2_vp_log, "card_2_returned_to_deck": card2_returned_log,
        "initial_draw": list(st.session_state.current_player_drawn_cards), # For reference/debugging
    }
    st.session_state.game_log.append(new_log_entry)

    # --- Advance Turn Logic ---
    user_is_first_player = st.session_state.user_goes_first
    # If current player was opponent AND user went first OR current player was user AND opponent went first
    # then this player was the second player of the Game Turn, so increment Game Turn.
    if (user_is_first_player and active_player == "opponent") or \
       (not user_is_first_player and active_player == "user"):
        st.session_state.current_game_turn += 1 # Advance to next game turn
        # Set active player for the new game turn based on who went first
        st.session_state.active_player_type = "user" if user_is_first_player else "opponent"
    else: # Current player was the first player of this Game Turn
        st.session_state.active_player_type = "opponent" if active_player == "user" else "user"
        
    reset_transient_turn_state() # Clear temporary data for the next player's actions
    st.session_state.turn_segment_in_progress = False # Reset flag

def calculate_total_scores():
    # Calculates and returns a dictionary of scores for both players, applying caps
    scores_dict = {ptype: {"raw_primary": 0, "raw_secondary": 0, "capped_primary": 0, 
                           "capped_secondary": 0, "paint_vp": 0, "total": 0} 
                   for ptype in ["user", "opponent"]}

    for player_key in ["user", "opponent"]:
        # Calculate raw primary VPs from the per-turn inputs
        scores_dict[player_key]["raw_primary"] = sum(st.session_state.all_primary_vps[player_key])
        # Apply the cap for total primary VPs
        scores_dict[player_key]["capped_primary"] = min(scores_dict[player_key]["raw_primary"], MAX_TOTAL_PRIMARY_VP)
        
        # Calculate raw secondary VPs from the game log
        current_raw_secondary = 0
        for entry_log in st.session_state.game_log:
            if entry_log["player_type"] == player_key:
                if entry_log["card_1_name"]: current_raw_secondary += entry_log["card_1_vp"]
                if entry_log["card_2_name"]: current_raw_secondary += entry_log["card_2_vp"]
        scores_dict[player_key]["raw_secondary"] = current_raw_secondary
        # Apply the cap for total secondary VPs
        scores_dict[player_key]["capped_secondary"] = min(scores_dict[player_key]["raw_secondary"], MAX_TOTAL_SECONDARY_VP)

        # Add paint bonus if selected
        if st.session_state.paint_vp_bonus_selected: 
            scores_dict[player_key]["paint_vp"] = PAINT_BONUS_VP
        
        # Calculate total score (capped primary + capped secondary + paint)
        scores_dict[player_key]["total"] = scores_dict[player_key]["capped_primary"] + \
                                           scores_dict[player_key]["capped_secondary"] + \
                                           scores_dict[player_key]["paint_vp"]
    return scores_dict

def calculate_projected_scores(current_scores_data):
    # Calculates projected final scores based on current performance and remaining turns
    projected_final_totals = {"user": current_scores_data["user"]["total"], 
                              "opponent": current_scores_data["opponent"]["total"]}
    
    for p_type_proj in ["user", "opponent"]:
        # Determine how many turns this player has completed based on unique game turns in log
        completed_turns_for_player = set()
        for log_item in st.session_state.game_log:
            if log_item["player_type"] == p_type_proj:
                completed_turns_for_player.add(log_item["game_turn"])
        num_player_turns_done = len(completed_turns_for_player)
        num_remaining_player_turns = MAX_GAME_TURNS - num_player_turns_done

        if num_remaining_player_turns > 0: # If there are turns left to project for
            if num_player_turns_done > 0: # If player has completed at least one turn
                # Calculate average raw scores per completed turn
                # Sum of primary VPs from `all_primary_vps` for turns that are in `completed_turns_for_player`
                raw_primary_from_done_turns = sum(st.session_state.all_primary_vps[p_type_proj][turn_idx-1] 
                                                  for turn_idx in completed_turns_for_player)
                # Raw secondary score is already summed in current_scores_data
                raw_secondary_from_done_turns = current_scores_data[p_type_proj]["raw_secondary"]
                
                avg_raw_primary_per_turn = raw_primary_from_done_turns / num_player_turns_done if num_player_turns_done > 0 else 0
                avg_raw_secondary_per_turn = raw_secondary_from_done_turns / num_player_turns_done if num_player_turns_done > 0 else 0
                
                # Project additional raw scores for remaining turns
                additional_projected_raw_primary = num_remaining_player_turns * avg_raw_primary_per_turn
                additional_projected_raw_secondary = num_remaining_player_turns * avg_raw_secondary_per_turn

                # Calculate final projected raw scores by adding current raw to projected additional raw
                final_proj_raw_primary = current_scores_data[p_type_proj]["raw_primary"] + additional_projected_raw_primary
                final_proj_raw_secondary = current_scores_data[p_type_proj]["raw_secondary"] + additional_projected_raw_secondary
                
                # Apply caps to these final projected raw scores
                final_proj_capped_primary = min(final_proj_raw_primary, MAX_TOTAL_PRIMARY_VP)
                final_proj_capped_secondary = min(final_proj_raw_secondary, MAX_TOTAL_SECONDARY_VP)
                
                # Add paint VP if applicable
                current_paint_vp = PAINT_BONUS_VP if st.session_state.paint_vp_bonus_selected else 0
                projected_final_totals[p_type_proj] = final_proj_capped_primary + final_proj_capped_secondary + current_paint_vp
            else: # No turns completed by this player yet, use a default projection
                # (e.g., 8 raw primary, 4 raw secondary per turn as a baseline)
                default_proj_raw_primary = num_remaining_player_turns * 8
                default_proj_raw_secondary = num_remaining_player_turns * 4
                
                final_proj_capped_primary = min(default_proj_raw_primary, MAX_TOTAL_PRIMARY_VP)
                final_proj_capped_secondary = min(default_proj_raw_secondary, MAX_TOTAL_SECONDARY_VP)
                current_paint_vp = PAINT_BONUS_VP if st.session_state.paint_vp_bonus_selected else 0
                projected_final_totals[p_type_proj] = final_proj_capped_primary + final_proj_capped_secondary + current_paint_vp
    return projected_final_totals

# --- UI Display Functions ---

def display_setup_screen():
    # UI for the initial game setup
    st.header("Game Setup")
    # Checkbox for who goes first
    st.checkbox("I will go first", value=st.session_state.get("setup_user_goes_first", True), key="setup_user_goes_first")
    # Checkbox for paint bonus VP
    st.checkbox(f"Start with {PAINT_BONUS_VP} 'Battle Ready' VP (Paint Bonus)", 
                value=st.session_state.get("setup_paint_vp_bonus", False), key="setup_paint_vp_bonus")
    # Checkbox to reset probabilities on new game
    st.checkbox("Reset card probabilities to default on new game start", 
                value=st.session_state.get("reset_probs_on_new_game", True), key="reset_probs_on_new_game")
    if st.button("Start Game"):
        start_new_game() # Initialize game with selected settings
        # Using st.rerun() instead of st.experimental_rerun() for modern Streamlit versions.
        # This might help if the 'ax' error is specific to the experimental version.
        st.rerun() 

def display_scoreboard_and_projections():
    # Displays the current scoreboard and projected scores in the sidebar
    scores_display_obj = calculate_total_scores() # Get current scores with all components
    st.sidebar.header("Scoreboard")

    for player_s_type in ["user", "opponent"]: # Loop for user and opponent
        player_s_label = "Your" if player_s_type == "user" else "Opponent's"
        # Detailed score breakdown: Capped Primary/Max, Capped Secondary/Max, Paint VP
        score_details_str = (f"P: {scores_display_obj[player_s_type]['capped_primary']}/{MAX_TOTAL_PRIMARY_VP}, "
                             f"S: {scores_display_obj[player_s_type]['capped_secondary']}/{MAX_TOTAL_SECONDARY_VP}")
        if st.session_state.paint_vp_bonus_selected: # Add paint VP info if applicable
            score_details_str += f", Paint: {PAINT_BONUS_VP}"
        st.sidebar.write(f"**{player_s_label} VP: {scores_display_obj[player_s_type]['total']}** ({score_details_str})")
    
    # Display projected scores if game is ongoing
    if st.session_state.game_started and st.session_state.current_game_turn <= MAX_GAME_TURNS :
        projected_scores_display = calculate_projected_scores(scores_display_obj)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Projected Final Scores")
        st.sidebar.write(f"Your Projected Total VP: **{projected_scores_display['user']:.0f}**")
        st.sidebar.write(f"Opponent's Projected Total VP: **{projected_scores_display['opponent']:.0f}**")

def display_current_turn_interface():
    # Main interface for handling the actions of the current player's turn
    active_player_name_full = "Your" if st.session_state.active_player_type == "user" else "Opponent's"
    active_player_name_short = "You" if st.session_state.active_player_type == "user" else "Opponent"
    st.header(f"Game Turn {st.session_state.current_game_turn} - {active_player_name_full} Actions")
    current_game_turn_idx = st.session_state.current_game_turn - 1 # 0-indexed

    # Section 0: Input Primary VP for the current player for this game turn
    st.subheader("0. Log Primary VP for this Turn")
    current_primary_score_for_turn = st.session_state.all_primary_vps[st.session_state.active_player_type][current_game_turn_idx]
    new_primary_score_for_turn = st.number_input(
        f"Primary VP scored by {active_player_name_short.lower()} in Turn {st.session_state.current_game_turn} (0-{MAX_PRIMARY_VP_PER_TURN_INPUT}):",
        min_value=0, max_value=MAX_PRIMARY_VP_PER_TURN_INPUT, value=current_primary_score_for_turn,
        key=f"current_primary_vp_input_{st.session_state.active_player_type}_{st.session_state.current_game_turn}"
    )
    # Update if value changes; optional immediate rerun for scoreboard update
    if new_primary_score_for_turn != current_primary_score_for_turn:
        st.session_state.all_primary_vps[st.session_state.active_player_type][current_game_turn_idx] = new_primary_score_for_turn
        # st.rerun() # Uncomment for immediate scoreboard update on primary VP change

    st.markdown("---") # Separator

    # Section 1: Choose Secondary Cards (if not already in progress for this turn segment)
    if not st.session_state.turn_segment_in_progress: 
        st.subheader("1. Choose Secondary Cards")
        card_selection_method = st.radio("Card Selection Method:", ("Randomly Draw", "Manually Select"), 
                               key=f"card_selection_method_{st.session_state.active_player_type}_{st.session_state.current_game_turn}")
        
        current_deck_available = get_available_deck()
        # Determine how many cards can actually be drawn (max 2, or fewer if deck is small)
        num_cards_can_draw = min(2, len(current_deck_available))

        if card_selection_method == "Randomly Draw":
            draw_button_label = f"Draw {num_cards_can_draw} Card(s)" if num_cards_can_draw > 0 else "Deck Empty"
            if st.button(draw_button_label, 
                         key=f"random_draw_button_{st.session_state.active_player_type}", 
                         disabled=(num_cards_can_draw == 0)): # Disable if no cards to draw
                draw_initial_cards_for_player(st.session_state.active_player_type, num_cards=num_cards_can_draw)
                st.rerun() # Rerun to show drawn cards
        else: # Manual Selection
            if not current_deck_available: st.warning("No cards left in deck to select.")
            else:
                # Max number of cards that can be manually selected
                num_can_select_manual = min(2, len(current_deck_available))
                manually_selected_cards = st.multiselect(f"Select up to {num_can_select_manual} card(s):", 
                                                           current_deck_available, max_selections=num_can_select_manual, 
                                                           key=f"manual_card_selection_{st.session_state.active_player_type}")
                if st.button("Confirm Manual Selection", key=f"confirm_manual_selection_button_{st.session_state.active_player_type}"):
                    # Validate selection: must select at least 1 and no more than allowed
                    if 0 < len(manually_selected_cards) <= num_can_select_manual:
                         manually_select_cards_for_player(manually_selected_cards)
                         st.rerun() # Rerun to show selected cards
                    else: st.warning(f"Please select between 1 and {num_can_select_manual} cards.")
        return # Stop here if in card selection phase; wait for user action

    # --- If turn_segment_in_progress is True (cards drawn/selected, proceed to mulligan/scoring) ---
    
    # Section 2: Display initially drawn/selected hand and offer mulligan
    initially_drawn_hand = st.session_state.current_player_drawn_cards
    st.subheader("2. Current Hand & Mulligan Option")
    st.write("Cards initially drawn/selected for this turn:")
    for card_item in initially_drawn_hand: st.markdown(f"- **{card_item}**")

    # Show EV and recommendation for user's hand
    if st.session_state.active_player_type == "user" and initially_drawn_hand:
        hand_ev_score = calculate_hand_ev(initially_drawn_hand, "user", st.session_state.current_game_turn)
        st.info(f"EV of initial hand (Turn {st.session_state.current_game_turn}): {hand_ev_score:.2f}. {get_ev_recommendation(hand_ev_score)}")

    # Mulligan option (only if cards were actually drawn/selected)
    if initially_drawn_hand: 
        cards_selected_for_mulligan = st.multiselect("Select cards from initial hand to discard & redraw (mulligan):", 
                                                     initially_drawn_hand, 
                                                     key=f"mulligan_selection_{st.session_state.active_player_type}")
        if st.button("Confirm Mulligan / Keep Initial Hand", key=f"mulligan_confirm_button_{st.session_state.active_player_type}"):
            if cards_selected_for_mulligan: mulligan_cards(cards_selected_for_mulligan) # Perform mulligan
            # If no cards selected for mulligan, current_player_final_hand remains as current_player_drawn_cards
            st.rerun() # Rerun to display the final hand after mulligan decision
    else: # Should not happen if turn_segment_in_progress is true without cards, but good fallback
        st.write("No cards were drawn or selected for this turn segment.")


    st.markdown("---") # Separator
    # Section 3: Display the final hand after mulligan (if any)
    st.subheader("3. Final Hand for Scoring This Turn")
    final_hand_to_score = st.session_state.current_player_final_hand
    if not final_hand_to_score: st.write("No cards in final hand to score.")
    else:
        for card_name_final in final_hand_to_score: st.markdown(f"- **{card_name_final}**")
    
    st.markdown("---") # Separator
    # Section 4: Input VPs for secondary cards and their disposition (kept/returned)
    st.subheader("4. Input Secondary VPs & Card Disposition")
    for card_name_scoring in final_hand_to_score: # Iterate through cards in the final hand
        # Ensure keys exist in session state for these inputs
        if card_name_scoring not in st.session_state.current_player_card_vps: 
            st.session_state.current_player_card_vps[card_name_scoring] = 0
        if card_name_scoring not in st.session_state.current_player_card_returned: 
            st.session_state.current_player_card_returned[card_name_scoring] = False
        
        input_cols = st.columns([3,2,2]) # Columns for layout
        with input_cols[0]: # VP input for the card
            st.session_state.current_player_card_vps[card_name_scoring] = st.number_input(
                f"VP for '{card_name_scoring}'", 0, VP_PER_SECONDARY_CARD_MAX, 
                value=st.session_state.current_player_card_vps.get(card_name_scoring,0), # Get current value or default
                key=f"vp_input_{card_name_scoring}_{st.session_state.active_player_type}_{st.session_state.current_game_turn}"
            )
        with input_cols[1]: # Checkbox for returning card to deck
            st.write(""); st.write("") # Vertical spacer for alignment
            st.session_state.current_player_card_returned[card_name_scoring] = st.checkbox(
                "Return to Deck?", value=st.session_state.current_player_card_returned.get(card_name_scoring,False),
                key=f"return_checkbox_{card_name_scoring}_{st.session_state.active_player_type}_{st.session_state.current_game_turn}",
                help="Check this if this card was not successfully scored or you want it available in the deck again."
            )
    
    st.markdown("---") # Separator
    # Button to end the current player's actions and log the turn
    if st.button(f"End {active_player_name_full} Actions & Log Turn", 
                 key=f"log_turn_button_{st.session_state.active_player_type}"):
        log_player_turn() # Log data and advance turn
        st.rerun() # Rerun to reflect next player/turn

def display_probability_settings():
    # UI for adjusting card scoring probabilities (per round) and CSV import/export
    with st.expander("Adjust Card Scoring Probabilities (Per Round)", expanded=False):
        st.caption("These probabilities affect the Expected Value (EV) calculation for the User's hand.")
        
        # Prepare data for CSV download (User's probabilities)
        user_probs_csv_data = []
        for card_name_csv, round_probs_csv in st.session_state.probabilities["user"].items():
            row_data = {"Card Name": card_name_csv}
            for r_csv in range(1, MAX_GAME_TURNS + 1): # Rounds 1-5
                row_data[f"Round {r_csv}"] = round_probs_csv.get(r_csv, 0.0) # Default to 0.0 if round missing
            user_probs_csv_data.append(row_data)
        user_probs_df = pd.DataFrame(user_probs_csv_data)
        # Download button for user probabilities
        st.download_button(label="Download User Probabilities (CSV)", 
                           data=user_probs_df.to_csv(index=False).encode('utf-8'),
                           file_name="user_card_probabilities.csv", mime="text/csv", 
                           key="download_user_probabilities_csv_button")

        # File uploader for user probabilities
        csv_upload_file = st.file_uploader("Upload User Probabilities (CSV File)", type="csv", 
                                           key="upload_user_probabilities_csv_uploader")
        if csv_upload_file is not None: # If a file is uploaded
            try:
                uploaded_df = pd.read_csv(csv_upload_file)
                # Initialize a structure to hold parsed probabilities, ensuring all cards/rounds have defaults
                new_parsed_probs = {cn_parse: {r_parse: 0.6 for r_parse in range(1, MAX_GAME_TURNS + 1)} for cn_parse in MASTER_DECK}
                for _, csv_row in uploaded_df.iterrows(): # Iterate through rows of uploaded CSV
                    card_name_from_csv = csv_row["Card Name"]
                    if card_name_from_csv in new_parsed_probs: # Only process if card is known
                        for r_from_csv in range(1, MAX_GAME_TURNS + 1): # For each round
                            # Get probability from CSV column "Round X", default to 0.6 if column missing/invalid
                            new_parsed_probs[card_name_from_csv][r_from_csv] = float(csv_row.get(f"Round {r_from_csv}", 0.6)) 
                st.session_state.probabilities["user"] = new_parsed_probs # Update user probabilities
                # Optionally, could also update opponent probabilities here if they should mirror user's after upload
                # st.session_state.probabilities["opponent"] = copy.deepcopy(new_parsed_probs) 
                st.success("User probabilities successfully uploaded from CSV!"); st.rerun()
            except Exception as e_csv: st.error(f"Error processing CSV file: {e_csv}")

        # Display sliders for adjusting probabilities for user and opponent
        for player_type_ui in ["user", "opponent"]:
            st.subheader(f"{player_type_ui.capitalize()}'s Probabilities")
            # Sort cards for consistent display (e.g., alphabetically)
            sorted_card_list_ui = sorted(MASTER_DECK) 
            for card_name_ui in sorted_card_list_ui:
                with st.expander(f"{card_name_ui}", expanded=False): # Collapsible section for each card
                    slider_cols = st.columns(MAX_GAME_TURNS) # Create columns for round sliders
                    for r_idx_ui, col_ui in enumerate(slider_cols):
                        game_round_ui = r_idx_ui + 1 # Current round (1-5)
                        # Get current probability for this card, player, round
                        current_prob_ui = st.session_state.probabilities[player_type_ui][card_name_ui].get(game_round_ui, 0.0)
                        # Slider for probability adjustment
                        new_prob_ui = col_ui.slider(f"T{game_round_ui}", 0.0, 1.0, current_prob_ui, step=0.01, 
                                                    key=f"prob_slider_{player_type_ui}_{card_name_ui}_r{game_round_ui}", 
                                                    label_visibility="collapsed") # Hide label for cleaner look
                        # Update probability in session state if changed
                        if new_prob_ui != current_prob_ui: 
                            st.session_state.probabilities[player_type_ui][card_name_ui][game_round_ui] = new_prob_ui
                            # Avoid immediate rerun on every slider change for performance; user can refresh or proceed

def display_all_primary_vp_input():
    # UI for editing all primary VPs across all turns for both players
    with st.expander(f"Edit All Primary VPs (Max {MAX_TOTAL_PRIMARY_VP} total from objectives, {MAX_PRIMARY_VP_PER_TURN_INPUT}/turn input limit)", expanded=False):
        for player_type_vp_edit in ["user", "opponent"]: # Loop for user and opponent
            st.subheader(f"{player_type_vp_edit.capitalize()}'s Primary VPs (Turns 1-5)")
            vp_input_cols = st.columns(MAX_GAME_TURNS) # Columns for each turn's input
            for turn_idx_vp_edit, col_vp_edit in enumerate(vp_input_cols):
                turn_num_display = turn_idx_vp_edit + 1 # Display turn number (1-5)
                current_vp_val = st.session_state.all_primary_vps[player_type_vp_edit][turn_idx_vp_edit]
                # Number input for primary VP for this turn
                new_vp_val = col_vp_edit.number_input(f"T{turn_num_display}", 0, MAX_PRIMARY_VP_PER_TURN_INPUT, 
                                                      value=current_vp_val,
                                                      key=f"all_primary_vp_edit_{player_type_vp_edit}_t{turn_num_display}", 
                                                      label_visibility="collapsed") # Hide label
                # Update if value changes
                if new_vp_val != current_vp_val: 
                    st.session_state.all_primary_vps[player_type_vp_edit][turn_idx_vp_edit] = new_vp_val
                    # Optional: st.rerun() for immediate scoreboard update
        # Button to manually refresh scores after edits if auto-rerun is not used on each input change
        if st.button("Refresh Scores After Primary VP Edits", key="refresh_primary_vp_edits_button"): 
            st.rerun()

def display_edit_past_scores(): 
    # UI for editing details of past logged turns (secondary card VPs and disposition)
    with st.expander("Edit Past Secondary Scores / Game Log Details", expanded=False):
        if not st.session_state.game_log: st.write("No game turns have been logged yet."); return # If log is empty
        
        # Iterate through game log in reverse (most recent first) for display
        for log_idx, logged_turn_data in reversed(list(enumerate(st.session_state.game_log))):
            player_label_log = logged_turn_data['player_type'].capitalize()
            st.markdown(f"---") # Separator for each log entry
            st.markdown(f"**Turn {logged_turn_data['game_turn']} - {player_label_log}** (Log ID: ...{logged_turn_data['log_id'][-6:]})") # Display turn info
            # Show primary VP that was logged for this specific turn segment (for reference)
            st.write(f"Primary VP logged for this player's actions in this turn: {logged_turn_data['primary_vp_logged_for_turn']}")
            
            # Edit details for Card 1 and Card 2 if they exist in the log entry
            for card_num_str, card_prefix_key in [("1", "card_1"), ("2", "card_2")]:
                card_name_key_log = f"{card_prefix_key}_name"
                card_vp_key_log = f"{card_prefix_key}_vp"
                card_returned_key_log = f"{card_prefix_key}_returned_to_deck"

                if logged_turn_data[card_name_key_log]: # If card exists in log
                    st.markdown(f"**Card: {logged_turn_data[card_name_key_log]}**")
                    edit_cols = st.columns([2,1]) # Layout columns
                    with edit_cols[0]: # VP input for this card
                        new_card_vp_log = st.number_input(f"VP", 0, VP_PER_SECONDARY_CARD_MAX, 
                                                          value=logged_turn_data[card_vp_key_log], 
                                                          key=f"edit_vp_{card_vp_key_log}_{logged_turn_data['log_id']}")
                        if new_card_vp_log != logged_turn_data[card_vp_key_log]: # Update if changed
                            st.session_state.game_log[log_idx][card_vp_key_log] = new_card_vp_log
                    with edit_cols[1]: # Checkbox for card returned status
                        new_card_returned_log = st.checkbox("Returned to Deck?", 
                                                            value=logged_turn_data[card_returned_key_log], 
                                                            key=f"edit_returned_{card_returned_key_log}_{logged_turn_data['log_id']}")
                        if new_card_returned_log != logged_turn_data[card_returned_key_log]: # Update if changed
                            st.session_state.game_log[log_idx][card_returned_key_log] = new_card_returned_log
        
        # Button to refresh scores after making edits in the log
        if st.button("Refresh Scores After Log Edits", key="refresh_secondary_log_edits_button"): 
            st.rerun()

# --- Main Application Flow ---
def main():
    # Main function to run the Streamlit application
    st.set_page_config(layout="wide") # Use wide layout for more space
    st.title("Warhammer 40k Game Simulator & Tracker") # Application title

    initialize_session_state() # Ensure all state variables are initialized

    if not st.session_state.game_started: # If game hasn't started, show setup screen
        display_setup_screen()
    else: # Game is in progress or over
        display_scoreboard_and_projections() # Display scoreboard in sidebar
        
        if st.session_state.current_game_turn > MAX_GAME_TURNS: # If game is over (all turns completed)
            st.header("Game Over!")
            st.balloons() # Fun celebration
            # Final scores are already shown by display_scoreboard_and_projections
            if st.button("Start New Game", key="game_over_start_new_game_button"): # Option to start new game
                st.session_state.game_started = False # Reset game started flag
                initialize_session_state() # Re-initialize state for a fresh game
                st.rerun()
        else: # Game is ongoing
            display_current_turn_interface() # Display main interface for current player's turn

        # Sections available throughout the game (and after) for editing and settings
        st.markdown("---"); display_all_primary_vp_input() # Edit all primary VPs
        st.markdown("---"); display_probability_settings() # Adjust card probabilities
        st.markdown("---"); display_edit_past_scores() # Edit past secondary scores from log
        
        # Sidebar option to start a new game at any time
        st.markdown("---"); st.sidebar.markdown("---")
        if st.sidebar.button("Start New Game (Resets Current Progress)", key="sidebar_start_new_game_button"):
            st.session_state.game_started = False # Reset flag
            initialize_session_state() # Re-initialize state
            st.rerun()

if __name__ == "__main__":
    main() # Run the main application function
