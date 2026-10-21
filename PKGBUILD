pkgname=python-repo2md
pkgver=0.1.2
pkgrel=1
pkgdesc="CLI tool to gather repo content into a single Markdown file for LLMs"
arch=('any')
url="https://github.com/Sapo534/repo2md"
license=('MIT')
depends=('python' 'python-questionary' 'python-pathspec')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("repo2md.py" "pyproject.toml")
sha256sums=('9594c36283cdbf52917efc1a141feb93a208b59bd33893eef3df524cd96a4259'
            '5823bf231c44814dc59dfd3c6d7f85a0088a3e61f22a3b08b5c1fc5b305c7891')

package() {
  cd "$srcdir"
  python -m build --wheel --no-isolation
  python -m installer --destdir="$pkgdir" dist/*.whl
}
