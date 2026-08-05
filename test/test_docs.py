import os
import unittest
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TestDocumentationDockerInstructions(unittest.TestCase):
    """Test suite ensuring Docker and GitHub Container Registry installation instructions are documented."""

    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.readme_path = os.path.join(self.root_dir, "readme.md")
        self.readme_it_path = os.path.join(self.root_dir, "readme-it.md")
        self.installation_doc_path = os.path.join(self.root_dir, "docs", "installation.md")

    def test_readme_contains_docker_ghcr_instructions(self):
        """Verify main readme.md contains Docker and GHCR image instructions."""
        logger.info("Verifying Docker/GHCR instructions in readme.md")
        self.assertTrue(os.path.exists(self.readme_path), "readme.md should exist")
        with open(self.readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ghcr.io/wip-sama/farmacy_solver:latest", content)
        self.assertIn("docker pull", content)
        self.assertIn("docker run", content)
        self.assertIn("docker compose", content)

    def test_readme_it_contains_docker_ghcr_instructions(self):
        """Verify Italian readme-it.md contains Docker and GHCR image instructions."""
        logger.info("Verifying Docker/GHCR instructions in readme-it.md")
        self.assertTrue(os.path.exists(self.readme_it_path), "readme-it.md should exist")
        with open(self.readme_it_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ghcr.io/wip-sama/farmacy_solver:latest", content)
        self.assertIn("docker pull", content)
        self.assertIn("docker run", content)
        self.assertIn("docker compose", content)

    def test_installation_doc_contains_docker_ghcr_instructions(self):
        """Verify docs/installation.md contains detailed Docker and GHCR deployment instructions."""
        logger.info("Verifying Docker/GHCR instructions in docs/installation.md")
        self.assertTrue(os.path.exists(self.installation_doc_path), "docs/installation.md should exist")
        with open(self.installation_doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ghcr.io/wip-sama/farmacy_solver:latest", content)
        self.assertIn("Method A: Pull & Run Pre-built Image from GitHub Container Registry (GHCR)", content)
        self.assertIn("docker pull", content)
        self.assertIn("docker run", content)

    def test_docker_compose_ghcr_file_exists(self):
        """Verify docker-compose.ghcr.yml exists and configures the GHCR image."""
        logger.info("Verifying docker-compose.ghcr.yml exists and uses ghcr image")
        ghcr_compose_path = os.path.join(self.root_dir, "docker-compose.ghcr.yml")
        self.assertTrue(os.path.exists(ghcr_compose_path), "docker-compose.ghcr.yml should exist")
        with open(ghcr_compose_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("image: ghcr.io/wip-sama/farmacy_solver:latest", content)

if __name__ == "__main__":
    unittest.main()
