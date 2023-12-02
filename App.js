// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import RegistrationComponent from './RegistrationComponent';

const App = () => {
  return (
    <Router>
      <Switch>
        <Route path="/register" component={RegistrationComponent} />
        {/* Add routes for login, workout logging, and nutrition logging components */}
      </Switch>
    </Router>
  );
};

export default App;
