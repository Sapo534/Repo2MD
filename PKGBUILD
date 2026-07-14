pkgname=python-repo2md
pkgver=0.1.1
pkgrel=1
pkgdesc="CLI tool to gather repo content into a single Markdown file for LLMs"
arch=('any')
url="https://github.com/Sapo534/repo2md"
license=('MIT')
depends=('python' 'python-questionary')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("repo2md.py" "pyproject.toml")
sha256sums=('756bbd47a0a7fb4dfa22c32515e6e09083ab16698e59c71268ed6b1fb5e16177'
            '87b2ae59909a8f931799f19ca7ab512528a8a7feb798c761bcc1f518bccffd4e')

package() {
    cd "$srcdir"
    python -m build --wheel --no-isolation
    python -m installer --destdir="$pkgdir" dist/*.whl
}
