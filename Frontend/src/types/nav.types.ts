type PageID = "feed" | "search" | "profile" | "admin";

interface NavItem {
  id: PageID;
  label: string;
  icon: string;
  activeIcon: string;
}

interface BottomNavProps {
  activePage: PageID;
  onPageChange: (page: PageID) => void;
  showAdmin?: boolean;
}
export { NavItem, BottomNavProps , PageID };