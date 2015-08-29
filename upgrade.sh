echo "Updating the tirukkural source..."
git pull -u origin master
sudo cp -r ./* /opt/tirukkural/
echo "Restarting the tirukkural service..."
sudo /etc/init.d/tirukkural restart
echo "Tirukkural service is updated and restarted..."