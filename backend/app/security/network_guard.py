import ipaddress
import urllib.parse
from typing import Set


class SecurityBoundaryViolation(Exception):
    """Raised when an outbound request attempts to violate the containment boundary."""
    pass


class NetworkGuard:
    """Enforces strict network containment for security laboratory testing.
    
    Refuses any outbound request to a non-local address, external domain,
    unauthorized port, or unapproved endpoint.
    """

    ALLOWED_SCHEMES: Set[str] = {"http"}
    ALLOWED_HOSTS: Set[str] = {"127.0.0.1", "localhost"}
    ALLOWED_PORTS: Set[int] = {8080}
    ALLOWED_ENDPOINT_PREFIXES: Set[str] = {
        "/login.php",
        "/setup.php",
        "/index.php",
        "/vulnerabilities/sqli/",
        "/vulnerabilities/xss_r/",
        "/vulnerabilities/exec/",
        "/vulnerabilities/fi/",
        "/security.php",
    }

    def __init__(self, target_host: str = "127.0.0.1", target_port: int = 8080) -> None:
        self.target_host = target_host
        self.target_port = target_port
        self._emergency_stop = False
        self._audit_log = []

    def trigger_emergency_stop(self) -> None:
        """Immediately halts all subsequent network requests."""
        self._emergency_stop = True

    def reset_emergency_stop(self) -> None:
        """Clears the emergency stop flag."""
        self._emergency_stop = False

    @property
    def is_stopped(self) -> bool:
        return self._emergency_stop

    def validate_destination(self, url: str) -> None:
        """Validates that a destination strictly targets the approved local practice container.
        
        Raises SecurityBoundaryViolation on any non-local, public, or unapproved target.
        """
        if self._emergency_stop:
            raise SecurityBoundaryViolation("Emergency stop active: all network operations rejected")

        if not url:
            raise SecurityBoundaryViolation("Empty destination URL")

        parsed = urllib.parse.urlsplit(url)

        if parsed.scheme.lower() not in self.ALLOWED_SCHEMES:
            raise SecurityBoundaryViolation(
                f"Unauthorized scheme '{parsed.scheme}'. Only local HTTP is permitted."
            )

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise SecurityBoundaryViolation("Missing hostname in destination URL")

        # Check loopback host identity
        if hostname not in self.ALLOWED_HOSTS:
            try:
                ip = ipaddress.ip_address(hostname)
                if not ip.is_loopback:
                    raise SecurityBoundaryViolation(
                        f"Target IP {hostname} is non-local. Laboratory is strictly loopback-contained."
                    )
            except ValueError:
                raise SecurityBoundaryViolation(
                    f"External hostname '{hostname}' rejected. Only local loopback is permitted."
                )

        # Port validation
        port = parsed.port if parsed.port is not None else 80
        if port not in self.ALLOWED_PORTS:
            raise SecurityBoundaryViolation(
                f"Port {port} rejected. Only approved target port {self.ALLOWED_PORTS} is permitted."
            )

        # Endpoint prefix validation
        path = parsed.path or "/"
        endpoint_allowed = any(
            path.startswith(prefix) for prefix in self.ALLOWED_ENDPOINT_PREFIXES
        )
        if not endpoint_allowed:
            raise SecurityBoundaryViolation(
                f"Path '{path}' is not within authorized laboratory test endpoints."
            )

    def filter_redirect(self, response, *args, **kwargs) -> None:
        """Requests hook to intercept and validate redirects before following them."""
        if response.is_redirect:
            location = response.headers.get("location")
            if location:
                # Resolve relative redirects against current URL
                resolved_url = urllib.parse.urljoin(response.url, location)
                self.validate_destination(resolved_url)
