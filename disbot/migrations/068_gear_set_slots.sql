-- V-16 phase 1 (owner decision Q-0092): the set-piece equipment model.
-- The single "armor" slot becomes four armor slots (helmet / chestplate /
-- leggings / boots) plus a dedicated "shield" slot, and the legacy
-- "armor" / "diamond armor" items fold into the chestplate tier family
-- ("iron chestplate" / "diamond chestplate" — tier vocabulary:
-- utils/equipment.py TIER_ORDER).  Direct-lane game state
-- (docs/ownership.md routes mining writes direct via utils/db/games/).
--
-- Order matters: rename items everywhere first, then re-slot.  Target names
-- and slots cannot collide with existing rows — neither existed before this
-- migration, and each player had at most one row in the old "armor" slot.

-- 1) Item renames (inventory, wear, equipment).
UPDATE mining_inventory SET item_name = 'iron chestplate' WHERE item_name = 'armor';
UPDATE mining_inventory SET item_name = 'diamond chestplate' WHERE item_name = 'diamond armor';
UPDATE mining_gear_wear SET item_name = 'iron chestplate' WHERE item_name = 'armor';
UPDATE mining_gear_wear SET item_name = 'diamond chestplate' WHERE item_name = 'diamond armor';
UPDATE mining_equipment SET item_name = 'iron chestplate' WHERE item_name = 'armor';
UPDATE mining_equipment SET item_name = 'diamond chestplate' WHERE item_name = 'diamond armor';

-- 2) Re-slot the old combined "armor" slot: shields get their own slot,
--    everything else that lived there is chest armor.
UPDATE mining_equipment SET slot = 'shield'
    WHERE slot = 'armor' AND item_name LIKE '%shield%';
UPDATE mining_equipment SET slot = 'chestplate' WHERE slot = 'armor';
