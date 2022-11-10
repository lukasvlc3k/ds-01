VAGRANTFILE_API_VERSION = "2"
# set docker as the default provider
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'
# disable parallellism so that the containers come up in order
ENV['VAGRANT_NO_PARALLEL'] = "1"
ENV['FORWARD_DOCKER_PORTS'] = "1"
# minor hack enabling to run the image and configuration trigger just once
ENV['VAGRANT_EXPERIMENTAL']="typed_triggers"

unless Vagrant.has_plugin?("vagrant-docker-compose")
  system("vagrant plugin install vagrant-docker-compose")
  puts "Dependencies installed, please try the command again."
  exit
end

# Node definitions
NODES  = { :nameprefix => "node-",  # node-1, node-2, ...
              :subnet => "10.161.0",
              :ip_offset => 100,  # nodes get IP addresses: 10.0.1.101, .102, .103, etc
              }

# Number of nodes to start:
NODES_COUNT = 3

# Common configuration
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
#
#   # Before the 'vagrant up' command is started, build docker images:
#   config.trigger.before :up, type: :command do |trigger|
#     trigger.name = "Build docker images and configuration files"
#     trigger.ruby do |env, machine|
#       # --- start of Ruby script ---
#       # Build image for backend nodes:
#       puts "Building backend node image:"
#       `docker build node -t "#{NODE_IMAGE}"`
#       # --- end of Ruby script ---
#     end
#   end

  config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".*/"
  config.ssh.insert_key = false

  # Definition of N nodes
  (1..NODES_COUNT).each do |i|
    node_ip_addr = "#{NODES[:subnet]}.#{NODES[:ip_offset] + i - 1}"
    node_name = "#{NODES[:nameprefix]}#{i}"
    # Definition of BACKEND
    config.vm.define node_name do |s|
      s.vm.network "private_network", ip: node_ip_addr
      s.vm.hostname = node_name
      s.vm.provider "docker" do |d|
        d.build_dir = "."
        d.name = node_name
        d.has_ssh = true
        d.env = {
            "IP_OFFSET": "#{NODES[:ip_offset]}",
            "NODE_ID" => i-1,
            "SERVER_PORT" => "12345",
            "IP_NETWORK": "#{NODES[:subnet]}",
            "NODES_COUNT": "#{NODES_COUNT}"
        }
      end
      s.vm.post_up_message = "Node #{node_name} up and running. You can access the node with 'vagrant ssh #{node_name}'}"
    end
  end

end

# EOF
