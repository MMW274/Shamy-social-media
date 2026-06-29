from pipeline.selector import DriveFile, select_asset


def make(name, folder, used=False):
    return DriveFile(id=name, name=name, folder=folder, mime_type="image/jpeg")


def test_picks_pillar_matching_file_for_amy_pillar():
    files = [
        make("amy_cozy_001.jpg", "01_safe_amy"),
        make("amy_play_002.jpg", "01_safe_amy"),
        make("amy_cozy_003.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick is not None
    assert pick.name == "amy_cozy_001.jpg"


def test_skips_used_assets():
    files = [
        make("amy_cozy_001.jpg", "01_safe_amy"),
        make("amy_cozy_002.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids={"amy_cozy_001.jpg"})
    assert pick.name == "amy_cozy_002.jpg"


def test_returns_none_when_no_match():
    files = [make("amy_play_001.jpg", "01_safe_amy")]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick is None


def test_rescue_glow_up_falls_back_to_any_safe_asset():
    files = [
        make("amy_window_001.jpg", "01_safe_amy"),
        make("sheldon_throne_002.jpg", "01_safe_sheldon"),
    ]
    pick = select_asset(files, pillar="rescue_glow_up", used_ids=set())
    assert pick is not None


def test_excludes_humans_folder_even_if_filename_matches():
    files = [
        make("amy_cozy_001.jpg", "02_humans_in_frame"),
        make("amy_cozy_002.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick.folder == "01_safe_amy"
