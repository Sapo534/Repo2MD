pkgname=python-repo2md
pkgver=0.1.0
pkgrel=1
pkgdesc="CLI tool to gather repo content into a single Markdown file for LLMs"
arch=('any')
url="https://github.com/youruser/repo2md"
license=('MIT')
depends=('python' 'python-questionary')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("repo2md.py" "pyproject.toml")
sha256sums=('SKIP' 'SKIP')

package() {
    cd "$srcdir"
    python -m build --wheel --no-isolation
    python -m installer --destdir="$pkgdir" dist/*.whl
}
