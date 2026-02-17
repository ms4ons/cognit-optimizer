#!/usr/bin/env python3
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'cognit-frontend', 'src'))

from db_manager import DBManager

TEST_DB_PATH = './tests/test_optimizer.db'


@pytest.fixture
def db():
    DBManager._instance = None
    DBManager._initialized = False
    
    db_dir = os.path.dirname(TEST_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    db_instance = DBManager(TEST_DB_PATH)
    
    yield db_instance
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    DBManager._instance = None
    DBManager._initialized = False


def test_optimizer_update_same_device_different_flavours(db):
    db.insert_device_assignment("device1", 1, "OVH", 101, {"FLAVOUR": "OVH"})
    db.insert_device_assignment("device1", 2, "AWS", 102, {"FLAVOUR": "AWS"})
    db.insert_device_assignment("device2", 3, "OVH", 103, {"FLAVOUR": "OVH"})
    
    allocations = {
        "device1:::OVH": 5,
        "device1:::AWS": 5,
        "device2:::OVH": 7,
    }
    
    all_assignments = db.get_all_device_assignments()
    assignment_lookup = {f"{a['device_id']}:::{a['flavour']}": a for a in all_assignments}
    
    updated_count = 0
    for composite_id, new_cluster_id in allocations.items():
        if ':::' not in composite_id:
            continue
        
        device_id, flavour = composite_id.split(':::', 1)
        current = assignment_lookup.get(composite_id)
        
        if current and current['cluster_id'] != new_cluster_id:
            db.update_device_assignment(
                device_id=device_id,
                cluster_id=new_cluster_id,
                flavour=flavour,
                app_req_id=current['app_req_id'],
                app_req_json=current['app_req_json']
            )
            updated_count += 1
    
    assert updated_count == 3
    
    ovh_assignment = db.get_device_assignment("device1", "OVH")
    aws_assignment = db.get_device_assignment("device1", "AWS")
    device2_assignment = db.get_device_assignment("device2", "OVH")
    
    assert ovh_assignment['cluster_id'] == 5
    assert aws_assignment['cluster_id'] == 5
    assert device2_assignment['cluster_id'] == 7


def test_optimizer_partial_update(db):
    db.insert_device_assignment("device1", 1, "OVH", 101, {"FLAVOUR": "OVH"})
    db.insert_device_assignment("device1", 2, "AWS", 102, {"FLAVOUR": "AWS"})
    
    allocations = {
        "device1:::OVH": 5,
        "device1:::AWS": 2,
    }
    
    all_assignments = db.get_all_device_assignments()
    assignment_lookup = {f"{a['device_id']}:::{a['flavour']}": a for a in all_assignments}
    
    updated_count = 0
    for composite_id, new_cluster_id in allocations.items():
        device_id, flavour = composite_id.split(':::', 1)
        current = assignment_lookup.get(composite_id)
        
        if current and current['cluster_id'] != new_cluster_id:
            db.update_device_assignment(
                device_id=device_id,
                cluster_id=new_cluster_id,
                flavour=flavour,
                app_req_id=current['app_req_id'],
                app_req_json=current['app_req_json']
            )
            updated_count += 1
    
    assert updated_count == 1
    
    ovh_assignment = db.get_device_assignment("device1", "OVH")
    aws_assignment = db.get_device_assignment("device1", "AWS")
    
    assert ovh_assignment['cluster_id'] == 5
    assert aws_assignment['cluster_id'] == 2


def test_get_all_assignments_for_optimizer(db):
    db.insert_device_assignment("device1", 1, "OVH", 101, {"FLAVOUR": "OVH"})
    db.insert_device_assignment("device1", 2, "AWS", 102, {"FLAVOUR": "AWS"})
    db.insert_device_assignment("device2", 1, "OVH", 103, {"FLAVOUR": "OVH"})
    
    assignments = db.get_all_device_assignments()
    
    assert len(assignments) == 3
    assert all('device_id' in a and 'flavour' in a for a in assignments)
    
    composite_ids = [f"{a['device_id']}:::{a['flavour']}" for a in assignments]
    assert "device1:::OVH" in composite_ids
    assert "device1:::AWS" in composite_ids
    assert "device2:::OVH" in composite_ids
