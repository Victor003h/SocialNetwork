<header className="sticky-top bg-dark border-bottom border-secondary p-3 shadow-sm">
  <div className="container d-flex align-items-center gap-3">
    <div
      className="rounded-circle bg-secondary"
      style={{
        width: 35,
        height: 35,
        backgroundImage: "url(https://i.pravatar.cc/300)",
        backgroundSize: "cover",
      }}
    ></div>
    <div className="flex-grow-1 position-relative">
      <input
        type="text"
        className="form-control form-control-sm bg-black text-white border-secondary rounded-pill ps-4"
        placeholder="Search distributed users..."
      />
    </div>
    <button className="btn btn-link text-primary p-0">
      <i className="bi bi-person-plus-fill fs-4"></i>
    </button>
  </div>
</header>;
