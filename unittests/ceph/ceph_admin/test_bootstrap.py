import mock
import pytest

from ceph.ceph_admin.bootstrap import construct_registry

RH_STAGE_CONFIG = {
    "credentials": {
        "registry": {
            "rh": {
                "cdn": {
                    "registry": "registry.redhat.io",
                    "username": "cdn-user",
                    "password": "cdn-pass",
                },
                "stage": {
                    "registry": "registry.stage.redhat.io",
                    "username": "qa@redhat.com",
                    "password": "stage-pass",
                },
            },
            "ibm": {
                "preprod": {
                    "registry": "cp.stg.icr.io",
                    "username": "preprod-user",
                    "password": "preprod-pass",
                }
            },
        }
    }
}


class TestConstructRegistry:
    @mock.patch("ceph.ceph_admin.bootstrap.get_cephci_config")
    def test_rh_quay_image_uses_credential_registry(self, mock_config):
        """RH nightly images live on quay.io; login must use the stage registry."""
        mock_config.return_value = RH_STAGE_CONFIG

        result = construct_registry(
            None,
            "quay.io",
            product="redhat",
            build_type="nightly",
        )

        assert "--registry-url registry.stage.redhat.io" in result
        assert "--registry-url quay.io" not in result
        assert "--registry-username qa@redhat.com" in result

    @mock.patch("ceph.ceph_admin.bootstrap.get_cephci_config")
    def test_rh_empty_registry_falls_back_to_credential_registry(self, mock_config):
        """bootstrap() passes an empty registry for RH so creds supply the login URL."""
        mock_config.return_value = RH_STAGE_CONFIG

        result = construct_registry(
            None,
            "",
            product="redhat",
            build_type="nightly",
        )

        assert "--registry-url registry.stage.redhat.io" in result
        assert "--registry-username qa@redhat.com" in result

    @mock.patch("ceph.ceph_admin.bootstrap.get_cephci_config")
    def test_rh_cdn_image_uses_cdn_credentials(self, mock_config):
        """A released image on registry.redhat.io uses the CDN credential block."""
        mock_config.return_value = RH_STAGE_CONFIG

        result = construct_registry(
            None,
            "registry.redhat.io",
            product="redhat",
            build_type="rc",
        )

        assert "--registry-url registry.redhat.io" in result
        assert "--registry-username cdn-user" in result
        assert "registry.stage.redhat.io" not in result

    @mock.patch("ceph.ceph_admin.bootstrap.get_cephci_config")
    def test_rh_stage_image_uses_stage_credentials(self, mock_config):
        """A stage image logs into registry.stage.redhat.io, not the CDN."""
        mock_config.return_value = RH_STAGE_CONFIG

        result = construct_registry(
            None,
            "registry.stage.redhat.io",
            product="redhat",
            build_type="rc",
        )

        assert "--registry-url registry.stage.redhat.io" in result
        assert "--registry-username qa@redhat.com" in result
        assert "--registry-url registry.redhat.io" not in result

    @mock.patch("ceph.ceph_admin.bootstrap.get_cephci_config")
    def test_ibm_preprod_uses_image_host(self, mock_config):
        """IBM preprod must login at the image host, not the credential registry field."""
        mock_config.return_value = RH_STAGE_CONFIG

        result = construct_registry(
            None,
            "preprod.icr.io",
            product="ibm",
            build_type="nightly",
        )

        assert "--registry-url preprod.icr.io" in result
        assert "--registry-url cp.stg.icr.io" not in result
        assert "--registry-username preprod-user" in result


if __name__ == "__main__":
    pytest.main([__file__])
