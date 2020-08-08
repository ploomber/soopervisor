from ploomberci import build


def test_build(tmp_sample_project):
    build.build_project('.')
