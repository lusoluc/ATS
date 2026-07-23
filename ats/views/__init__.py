"""SecurATS View-Paket.

Die frueher 6.200-zeilige views.py ist in Domaenen-Module zerlegt. Dieses
Paket re-exportiert alle Namen, damit `from ats import views` und
`views.X` in urls.py sowie bestehende Importe unveraendert weiterlaufen.
Sicherheitsrelevant: jede View traegt ihren eigenen Auth-Decorator –
es gibt KEINE globale Login-Middleware (siehe SECURITY_AUDIT.md).
"""

from .admin_pages import *  # noqa: F401,F403
from .ai import *  # noqa: F401,F403
from .analytics_views import *  # noqa: F401,F403
from .applications import *  # noqa: F401,F403
from .auth_views import *  # noqa: F401,F403
from .cms import *  # noqa: F401,F403
from .common import *  # noqa: F401,F403
from .feeds import *  # noqa: F401,F403
from .governance import *  # noqa: F401,F403
from .interviews import *  # noqa: F401,F403
from .jobs import *  # noqa: F401,F403
from .public import *  # noqa: F401,F403
from .search import *  # noqa: F401,F403
from .settings_admin import *  # noqa: F401,F403
