type PageID = "feed" | "search" | "alerts" | "friends" | "profile";

interface NavItem {
  id: PageID;
  label: string;
  icon: string;
  activeIcon: string;
}

interface BottomNavProps {
  activePage: PageID;
  onPageChange: (page: PageID) => void;
}
export { NavItem, BottomNavProps , PageID };