"""Recurring tasks used to organize the project.

http://www.pyinvoke.org/

"""

from invoke import task


@task()
def examples(c):
    """Compose bundled example YAML files."""
    c.run('make example/a{1,2,3}_*.yaml')


@task()
def clean(c):
    """Destroy prior artifacts."""
    c.run('rm -rf build src/*.egg-info', warn=True)
    c.run('rm dist/*', warn=True)
    c.run('rmdir dist', warn=True)
    c.run(r'find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf')


@task(pre=[clean])
def build(c):
    """Build wheel in dist/."""
    c.run('python -m build')


@task(pre=[build])
def test(c):
    """Build, install, and then run unit tests."""
    with c.cd('dist'):
        c.run('sudo pip install --force-reinstall *.whl')
    c.run('pytest')


@task()
def deploy(c):
    """Upload all artifacts in dist/ to PyPI."""
    c.run('twine upload dist/*')
