import pytest
import cv2
import numpy as np
from src.video_trimmer import getKeyframes, generateReferenceFrame

class TestGetKeyFrames:
    def test_file_not_found(self):
        with pytest.raises(RuntimeError) as e_info:
            getKeyframes("foobarbazz")
        assert "No such file" in str(e_info.value)

    def test_bad_file(self):
        with pytest.raises(RuntimeError) as e_info:
            getKeyframes("src/video_trimmer.py")
        assert "Invalid data found" in str(e_info.value)

    def test_waves(self):
        result = getKeyframes("assets/waves.mp4")
        assert result == [float(x) for x in range(0, 35, 2)]

    def test_waves_intro(self):
        result = getKeyframes("assets/waves_intro.mp4")
        assert result == [0.0]

class TestGenerateReferenceFrame:
    @pytest.mark.parametrize("file,coords,frame", [('assets/waves_intro_screen.png', [0,-1,0,65], 5), ('assets/waves_outro_screen.png', [0,-1,530,-1], 512)])
    def test_waves_frame(self, file, coords, frame):
        toComp = cv2.imread(file)
        res = generateReferenceFrame("assets/waves.mp4", coords, frame=frame)
        assert np.array_equal(toComp, res)

    @pytest.mark.parametrize("file,coords,ts", [('assets/waves_intro_screen.png', [0,-1,0,65], 5/16), ('assets/waves_outro_screen.png', [0,-1,530,-1], 512/16)])
    def test_waves_timestamp(self, file, coords, ts):
        toComp = cv2.imread(file)
        res = generateReferenceFrame("assets/waves.mp4", coords, timestamp=ts)
        assert np.array_equal(toComp, res)
