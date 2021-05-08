from soopervisor import build


def test_build(tmp_sample_project):
    build.build_project('soopervisor.yaml',
                        env_name='env',
                        clean_products_path=False,
                        dry_run=False)
