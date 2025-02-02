<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tree Data Structure</title>
  <style>
    /* General tree structure styles */
    .tree ul {
      padding-top: 20px;
      position: relative;
      transition: all 0.5s;
    }
    
    .tree li {
      float: left;
      text-align: center;
      list-style-type: none;
      position: relative;
      padding: 20px 5px 0 5px;
      transition: all 0.5s;
    }
    
    /* Connecting lines */
    .tree li::before, .tree li::after {
      content: '';
      position: absolute;
      top: 0;
      right: 50%;
      border-top: 2px solid #ccc;
      width: 50%;
      height: 20px;
    }
    
    .tree li::after {
      right: auto;
      left: 50%;
      border-left: 2px solid #ccc;
    }
    
    /* Nodes */
    .tree li:only-child::after, .tree li:only-child::before {
      display: none;
    }
    
    .tree li:only-child {
      padding-top: 0;
    }
    
    .tree li:first-child::before, .tree li:last-child::after {
      border: 0 none;
    }
    
    .tree li:last-child::before {
      border-right: 2px solid #ccc;
    }
    
    /* Node appearance */
    .tree li div {
      border: 2px solid #ccc;
      padding: 10px;
      display: inline-block;
      border-radius: 5px;
      background-color: white;
      position: relative;
    }

    .tree li div:hover {
      background-color: #e6f2ff;
      border-color: #0073e6;
    }
    
    /* Hover animation */
    .tree li div:hover + ul li div {
      background-color: #f9f9f9;
      border-color: #0073e6;
    }
  </style>
</head>
<body>

  <div class="tree">
    <ul>
      <li>
        <div>Root</div>
        <ul>
          <li>
            <div>Node 1</div>
            <ul>
              <li><div>Child 1</div></li>
              <li><div>Child 2</div></li>
            </ul>
          </li>
          <li>
            <div>Node 2</div>
            <ul>
              <li><div>Child 3</div></li>
              <li><div>Child 4</div></li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>
  </div>

</body>
</html>

